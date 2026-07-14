import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY is not set. Create a .env file in the project root with:\n"
        "OPENAI_API_KEY=sk-..."
    )

MODEL_NAME = os.environ.get("ROUTER_MODEL", "gpt-5.4-mini")
LOG_LEVEL = os.environ.get("ROUTER_LOG_LEVEL", "INFO")

LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "router.log"

TICKET_PREVIEW_LENGTH = 80  # chars of ticket text shown in log lines


#DATABASE URL
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://wasi@localhost:5432/ticket_router",  # local dev default
)