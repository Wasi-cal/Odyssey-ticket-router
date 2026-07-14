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

import config

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