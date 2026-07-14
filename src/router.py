import logging
import time
from typing import Literal

from pydantic import BaseModel
from openai import OpenAI

import config
from taxonomy import CATEGORIES, PRIORITIES, PRIORITY_DEFINITIONS
from validator import validate, resolve

client = OpenAI(api_key=config.OPENAI_API_KEY)

logging.basicConfig(
    filename=str(config.LOG_FILE),
    level=config.LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logger = logging.getLogger("router")


def build_system_prompt():
    category_lines = "\n".join(f"- {c['id']}: {c['description']}" for c in CATEGORIES)
    priority_lines = "\n".join(f"- {level}: {desc}" for level, desc in PRIORITY_DEFINITIONS.items())
    return f"""You are a support ticket classifier for an AI startup's support desk.

Classify each ticket into exactly one of these categories:
{category_lines}

Assign a priority using these definitions:
{priority_lines}

A calm or professional tone does not lower priority below what the issue's
severity warrants — assess priority from the issue itself, not the reporter's tone.
An angry or frustrated tone raises priority but never changes category.

When a ticket is phrased as a "how do I..." question, don't default to
general_inquiry just because of the phrasing. Ask instead: is this about the
requester's own account, workspace, data, or a technical constraint/error they
are personally hitting? If so, classify by that topic (api_integration,
account_access, billing, etc.) even though it's phrased as a how-to question.
Mentioning a specific endpoint, SDK method, or feature name does NOT by itself
make something api_integration — a question can name a specific endpoint and
still be a general "how does this mechanism work" documentation question.
general_inquiry is for questions answerable purely from documentation, with
nothing tied to the requester's specific account or workspace.

Examples of correct classification for tricky cases:

Ticket: "How does streaming work with the SDK?"
category: general_inquiry
(A conceptual documentation question with nothing specific to their account or
plan — stays general_inquiry even though it mentions the SDK.)

Ticket: "How do I paginate through results from the /v1/list-runs endpoint
using the SDK?"
category: general_inquiry
(Asks how a general API mechanism works and how to use it — documentation-
answerable, not tied to their account, plan, or an error they're hitting.
Naming a specific endpoint does not by itself make this api_integration.)

Ticket: "What's the rate limit for API calls on the free tier?"
category: api_integration
(Asks about a specific technical constraint tied to their account/plan, not a
conceptual how-it-works question — api_integration, even phrased as how-to.)

Ticket: "How do I make a teammate an admin in our workspace?"
category: account_access
(NOT general_inquiry — questions about permissions, roles, or admin assignment
belong to account_access even when phrased as a how-to question rather than an
error report.)

Ticket: "Can I merge two workspaces into one account? We accidentally created
a duplicate org."
category: account_access
(NOT general_inquiry — workspace/org structure and membership questions are
account_access, since they concern managing the requester's own account setup,
not a conceptual product question.)

Only use general_inquiry when the ticket's topic doesn't match any other
category at all and has nothing to do with the requester's own account,
workspace, or data — e.g. broad product questions, documentation lookups, or
pre-sales questions unrelated to API, account, or billing specifics.

Return the category, the priority, and a one-line reasoning for your choice."""
SYSTEM_PROMPT = build_system_prompt()

CategoryLiteral = Literal[tuple(c["id"] for c in CATEGORIES)]
PriorityLiteral = Literal[tuple(PRIORITIES)]


class TicketClassification(BaseModel):
    category: CategoryLiteral
    priority: PriorityLiteral
    reasoning: str

def route_ticket(ticket_text: str) -> dict | str:
    try:
        response = client.beta.chat.completions.parse(
            model=config.MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": ticket_text},
            ],
            response_format=TicketClassification,
        )
    except Exception as e:
        logger.error("LLM call failed: %s", e)
        return f"router call failed: {e}"

    message = response.choices[0].message
    if message.parsed is None:
        logger.warning("model refused to classify: %s", message.refusal)
        return f"model refused to classify: {message.refusal}"

    return message.parsed.model_dump()


def _preview(ticket_text: str, length: int = config.TICKET_PREVIEW_LENGTH) -> str:
    """This function is used to add the first 80 characters to the logs"""
    flat = ticket_text.replace("\n", " ")
    return flat[:length] + ("..." if len(flat) > length else "")


def classify(ticket_text: str):
    """Single reusable router pipeline: call the LLM, retry once if the
    response fails validation, then fall back to the safe default. Returns a
    validator.ResolvedResult - .result is the final
    {category, priority, team, reasoning} dict. Used by both the harness and
    the CLI so retry/fallback behavior is identical and tested in one place."""
    start = time.perf_counter()
    preview = _preview(ticket_text)

    attempts = [route_ticket(ticket_text)]
    first_check = validate(attempts[-1])
    if not first_check.is_valid:
        logger.warning("attempt 1 failed validation (%s) for %r - retrying", first_check.errors, preview)
        attempts.append(route_ticket(ticket_text))

    resolved = resolve(attempts)
    elapsed_ms = (time.perf_counter() - start) * 1000

    if resolved.used_fallback:
        logger.error(
            "FALLBACK fired after %d attempt(s), %.0fms, for %r - last errors: %s",
            resolved.attempts_tried, elapsed_ms, preview, resolved.errors,
        )
    else:
        logger.info(
            "routed -> category=%s priority=%s team=%s (%d attempt(s), %.0fms) for %r",
            resolved.result["category"], resolved.result["priority"], resolved.result["team"],
            resolved.attempts_tried, elapsed_ms, preview,
        )

    return resolved