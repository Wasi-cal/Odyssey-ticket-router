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


@app.post("/classify")
async def classify_ticket(payload: MessagePayload):
    text = payload.ticket.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Ticket text is empty.")

    start = time.perf_counter()
    resolved = classify(text)
    latency_ms = (time.perf_counter() - start) * 1000

    ticket_id = insert_ticket(title=text[:80], description=text, resolved=resolved)

    return {
        "ticket_id": ticket_id,
        **resolved.result,
        "used_fallback": resolved.used_fallback,
        "attempts_tried": resolved.attempts_tried,
        "latency_ms": round(latency_ms, 1),
    }