"""Postgres connection pool (psycopg 3, sync).

The pool is created here but NOT opened - `main.py` opens it at app startup
and closes it at shutdown (see the lifespan handler) so the pool's lifecycle
tracks the app's. Check out a connection per unit of work:

    from db import get_conn

    with get_conn() as conn:              # returned to the pool on exit
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            row = cur.fetchone()

Rows come back as dicts (dict_row), so `row["category_id"]` works.
"""

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

import config as config

pool = ConnectionPool(
    conninfo=config.DATABASE_URL,
    min_size=1,
    max_size=10,
    open=False,                       # opened explicitly in main.py's lifespan
    kwargs={"row_factory": dict_row},
)


def get_conn():
    """Check out a pooled connection. Use as a context manager:
    `with get_conn() as conn:` - the connection is returned to the pool
    automatically when the block exits."""
    return pool.connection()


_PRIORITY_TO_ROLE = {"High": "Senior Specialist", "Medium": "Specialist", "Low": "Associate"}

def insert_ticket(description: str, resolved, submitted_by: str) -> str:
    result = resolved.result
    role = _PRIORITY_TO_ROLE[result["priority"]]

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT e.employee_id
                FROM employee e
                JOIN category c ON c.team_id = e.team_id
                LEFT JOIN ticket t
                    ON t.assigned_to = e.employee_id
                    AND t.status NOT IN ('Resolved', 'Closed')
                WHERE c.category_id = %s AND e.role = %s
                GROUP BY e.employee_id
                ORDER BY COUNT(t.id) ASC, e.employee_id ASC
                LIMIT 1
                """,
                (result["category"], role),
            )
            row = cur.fetchone()
            assigned_to = row["employee_id"] if row else None

            cur.execute(
                """
                INSERT INTO ticket
                    (title, description, category_id, priority, reasoning,
                     assigned_to, submitted_by, estimated_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING ticket_ref
                """,
                (result["title"], description, result["category"], result["priority"],
                 result["reasoning"], assigned_to, submitted_by, result["estimated_time"]),
            )
            return cur.fetchone()["ticket_ref"]
        