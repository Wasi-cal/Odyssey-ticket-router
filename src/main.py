import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "src" / "taxonomy"))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from router import classify
from db import pool, insert_ticket


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool.open()
    pool.wait()
    try:
        yield
    finally:
        pool.close()


app = FastAPI(
    title="Smart Ticket Router",
    description="Classifies a support ticket into category / priority / team with a one-line reasoning.",
    lifespan=lifespan,
)


class MessagePayload(BaseModel):
    ticket: str = Field(min_length=1, max_length=8000)


@app.get("/")
async def index():
    return {"service": "Smart Ticket Router", "docs": "/docs", "classify": "POST /classify"}


class TicketPayload(BaseModel):
    submitted_by: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=1, max_length=8000)


@app.post("/tickets", status_code=201)
async def create_ticket(payload: TicketPayload):
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Ticket text is empty.")
    resolved = classify(text)
    ticket_ref = insert_ticket(description=text, resolved=resolved, submitted_by=payload.submitted_by)
    return await get_ticket(ticket_ref)


@app.get("/tickets")
async def list_tickets(submitted_by: str):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT t.ticket_ref, t.title, c.label AS category_label,
                       t.priority, t.status, t.updated_at
                FROM ticket t JOIN category c ON c.category_id = t.category_id
                WHERE t.submitted_by = %s
                ORDER BY t.updated_at DESC
                """,
                (submitted_by,),
            )
            return {"tickets": cur.fetchall()}


@app.get("/tickets/{ticket_ref}")
async def get_ticket(ticket_ref: str):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT t.ticket_ref, t.title, t.description, t.category_id AS category,
                       c.label AS category_label, t.priority, t.status, tm.team_name AS team,
                       t.estimated_time, t.reasoning, t.created_at, t.updated_at,
                       e.name AS assigned_name, e.role AS assigned_role,
                       mgr.name AS manager_name, mgr.role AS manager_role
                FROM ticket t
                JOIN category c ON c.category_id = t.category_id
                JOIN team tm ON tm.team_id = c.team_id
                LEFT JOIN employee e ON e.employee_id = t.assigned_to
                LEFT JOIN employee mgr ON mgr.employee_id = e.reports_to
                WHERE t.ticket_ref = %s
                """,
                (ticket_ref,),
            )
            row = cur.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Ticket not found.")
            return {
                **{k: row[k] for k in ("ticket_ref","title","description","category",
                    "category_label","priority","status","team","estimated_time",
                    "reasoning","created_at","updated_at")},
                "assigned_to": {"name": row["assigned_name"], "role": row["assigned_role"]} if row["assigned_name"] else None,
                "reports_to": {"name": row["manager_name"], "role": row["manager_role"]} if row["manager_name"] else None,
            }