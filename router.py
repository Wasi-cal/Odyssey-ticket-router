import os
from dotenv import load_dotenv
from pydantic import BaseModel
from openai import OpenAI
from taxonomy import CATEGORIES, PRIORITY_DEFINITIONS
from validator import validate, resolve

load_dotenv()
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


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

class TicketClassification(BaseModel):
    category: str
    priority: str
    reasoning: str

def route_ticket(ticket_text: str) -> dict | str:
    try:
        response = client.beta.chat.completions.parse(
            model="gpt-5.4-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": ticket_text},
            ],
            response_format=TicketClassification,
        )
    except Exception as e:
        return f"router call failed: {e}"

    message = response.choices[0].message
    if message.parsed is None:
        return f"model refused to classify: {message.refusal}"

    return message.parsed.model_dump()


def classify(ticket_text: str):
    """Single reusable router pipeline: call the LLM, retry once if the
    response fails validation, then fall back to the safe default. Returns a
    validator.ResolvedResult - .result is the final
    {category, priority, team, reasoning} dict. Used by both the harness and
    the CLI so retry/fallback behavior is identical and tested in one place."""
    attempts = [route_ticket(ticket_text)]
    if not validate(attempts[-1]).is_valid:
        attempts.append(route_ticket(ticket_text))
    return resolve(attempts)