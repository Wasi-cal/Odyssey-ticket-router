import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "backend" / "src"))

from validator import FALLBACK_RESULT, ResolvedResult
from db import insert_ticket

fake_resolved = ResolvedResult(
    result=dict(FALLBACK_RESULT),
    used_fallback=True,
    attempts_tried=2,
    errors=["simulated failure for testing"],
)
ticket_id = insert_ticket(title="test fallback insert", description="simulated fallback test", resolved=fake_resolved)
print("Inserted fallback ticket as id:", ticket_id)