import os
from dotenv import load_dotenv
from pydantic import BaseModel
from openai import OpenAI
from taxonomy import CATEGORIES, PRIORITY_DEFINITIONS

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

Examples of correct classification for tricky cases:

Ticket: "How does streaming work with the SDK?"
category: general_inquiry
(A conceptual documentation question with nothing specific to their account or
plan — stays general_inquiry even though it mentions the SDK.)

Ticket: "What's the rate limit for API calls on the free tier?"
category: api_integration
(Asks about a specific technical constraint tied to their account/plan, not a
conceptual how-it-works question — api_integration, even phrased as how-to.)

Ticket: "How do I make a teammate an admin in our workspace?"
category: account_access
(NOT general_inquiry — questions about permissions, roles, or admin assignment
belong to account_access even when phrased as a how-to question rather than an
error report.)

Only use general_inquiry when the ticket's topic doesn't match any other
category at all — e.g. broad product questions, documentation lookups, or
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