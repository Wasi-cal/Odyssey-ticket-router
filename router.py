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

Return the category, the priority, and a one-line reasoning for your choice."""

SYSTEM_PROMPT = build_system_prompt()

class TicketClassification(BaseModel):
    category: str
    priority: str
    reasoning: str

def route_ticket(ticket_text: str) -> dict:
    response = client.beta.chat.completions.parse(
        model="gpt-5.4-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": ticket_text},
        ],
        response_format=TicketClassification,
    )
    return response.choices[0].message.parsed.model_dump()