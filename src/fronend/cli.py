import json
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "src" / "taxonomy"))

from router import classify


def read_ticket() -> str | None:
    """Reads a (possibly multi-line) ticket; blank line submits. Returns None
    on 'quit'/'exit' or EOF/Ctrl+C."""
    lines = []
    try:
        while True:
            line = input("Ticket: " if not lines else "...     ")
            if not lines and line.strip().lower() in ("quit", "exit"):
                return None
            if not line:
                break
            lines.append(line)
    except (EOFError, KeyboardInterrupt):
        print()
        return None
    return "\n".join(lines).strip()


def process_ticket(text: str) -> dict:
    start = time.perf_counter()
    resolved = classify(text)
    latency_ms = (time.perf_counter() - start) * 1000

    result = dict(resolved.result)
    result["latency_ms"] = round(latency_ms, 1)
    return result


def main():
    print("Smart Ticket Router — paste a ticket (blank line to submit), or type 'quit' to exit.\n")
    while True:
        text = read_ticket()
        if text is None:
            break
        if not text:
            continue
        print(json.dumps(process_ticket(text), indent=2))
        print()


if __name__ == "__main__":
    main()
