import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "backend" / "src"))

import jwt
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from psycopg.errors import UniqueViolation
from pydantic import BaseModel, Field

from router import classify
from db import pool, insert_ticket
from auth.auth import authenticate_user, create_access_token, create_user, decode_access_token

security = HTTPBearer()


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
    text: str = Field(min_length=1, max_length=8000)


class ClassifyPayload(BaseModel):
    text: str = Field(min_length=1, max_length=8000)


class RegisterPayload(BaseModel):
    email: str = Field(min_length=3, max_length=200)
    password: str = Field(min_length=8, max_length=200)


class LoginPayload(BaseModel):
    email: str = Field(min_length=3, max_length=200)
    password: str = Field(min_length=1, max_length=200)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    try:
        return decode_access_token(credentials.credentials)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")


@app.post("/auth/register", status_code=201)
async def register(payload: RegisterPayload):
    email = payload.email.strip().lower()
    try:
        user_id = create_user(email, payload.password)
    except UniqueViolation:
        raise HTTPException(status_code=409, detail="Email already registered.")
    token = create_access_token(user_id, email)
    return {"access_token": token, "token_type": "bearer"}


@app.post("/auth/login")
async def login(payload: LoginPayload):
    user = authenticate_user(payload.email.strip().lower(), payload.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    token = create_access_token(user["user_id"], user["email"])
    return {"access_token": token, "token_type": "bearer"}


@app.post("/classify")
async def classify_only(payload: ClassifyPayload):
    """Runs the same classification pipeline as POST /tickets but never
    touches the database - used by the AI-vs-manual comparison page to
    classify tickets live without creating real ticket rows."""
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Ticket text is empty.")
    resolved = classify(text)
    return {**resolved.result, "used_fallback": resolved.used_fallback}


@app.post("/tickets", status_code=201)
async def create_ticket(payload: TicketPayload, current_user: dict = Depends(get_current_user)):
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Ticket text is empty.")
    resolved = classify(text)
    ticket_ref = insert_ticket(
        description=text,
        resolved=resolved,
        submitted_by=current_user["email"],
        submitted_by_user_id=int(current_user["sub"]),
    )
    return await get_ticket(ticket_ref, current_user)


@app.get("/tickets")
async def list_tickets(current_user: dict = Depends(get_current_user)):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT t.ticket_ref, t.title, c.label AS category_label,
                       t.priority, t.status, t.updated_at, t.reasoning,
                       e.name AS assigned_to, mgr.name AS reports_to
                FROM ticket t
                JOIN category c ON c.category_id = t.category_id
                LEFT JOIN employee e ON e.employee_id = t.assigned_to
                LEFT JOIN employee mgr ON mgr.employee_id = COALESCE(e.reports_to, e.employee_id)
                WHERE t.submitted_by_user_id = %s
                ORDER BY t.updated_at DESC
                """,
                (int(current_user["sub"]),),
            )
            return {"tickets": cur.fetchall()}


@app.get("/tickets/{ticket_ref}")
async def get_ticket(ticket_ref: str, current_user: dict = Depends(get_current_user)):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT t.ticket_ref, t.title, t.description, t.category_id AS category,
                       c.label AS category_label, t.priority, t.status, tm.team_name AS team,
                       t.estimated_time, t.reasoning, t.created_at, t.updated_at,
                       t.submitted_by_user_id,
                       e.name AS assigned_name, e.role AS assigned_role,
                       mgr.name AS manager_name, mgr.role AS manager_role
                FROM ticket t
                JOIN category c ON c.category_id = t.category_id
                JOIN team tm ON tm.team_id = c.team_id
                LEFT JOIN employee e ON e.employee_id = t.assigned_to
                LEFT JOIN employee mgr ON mgr.employee_id = COALESCE(e.reports_to, e.employee_id)
                WHERE t.ticket_ref = %s
                """,
                (ticket_ref,),
            )
            row = cur.fetchone()
            if row is None or row["submitted_by_user_id"] != int(current_user["sub"]):
                raise HTTPException(status_code=404, detail="Ticket not found.")
            return {
                **{k: row[k] for k in ("ticket_ref","title","description","category",
                    "category_label","priority","status","team","estimated_time",
                    "reasoning","created_at","updated_at")},
                "assigned_to": {"name": row["assigned_name"], "role": row["assigned_role"]} if row["assigned_name"] else None,
                "reports_to": {"name": row["manager_name"], "role": row["manager_role"]} if row["manager_name"] else None,
            }