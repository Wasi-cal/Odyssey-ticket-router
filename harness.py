import time
from dataclasses import dataclass, field

from tickets import ALL_TICKETS
from validator import validate, resolve, FALLBACK_RESULT


@dataclass
class TicketOutcome:
    ticket_id: str
    passed: bool
    latency_s: float
    validation_errors: list
    got: dict | None
    notes: list = field(default_factory=list)


def run_harness(router_fn, tickets=ALL_TICKETS):
    outcomes = []
    for ticket in tickets:
        start = time.perf_counter()
        raw = router_fn(ticket.text)
        latency = time.perf_counter() - start

        outcome = validate(raw)
        notes = []
        passed = outcome.is_valid
        got = outcome.result if outcome.is_valid else None

        if outcome.is_valid:
            if ticket.expected_category is not None and got["category"] != ticket.expected_category:
                passed = False
                notes.append(f"expected category {ticket.expected_category!r}, got {got['category']!r}")
            if ticket.expected_priorities is not None and got["priority"] not in ticket.expected_priorities:
                passed = False
                notes.append(
                    f"expected priority in {sorted(ticket.expected_priorities)}, got {got['priority']!r}"
                )

        outcomes.append(TicketOutcome(
            ticket_id=ticket.id,
            passed=passed,
            latency_s=latency,
            validation_errors=outcome.errors,
            got=got,
            notes=notes,
        ))
    return outcomes


def test_fallback_on_malformed_response():
    """Confirms the deterministic retry-then-fallback logic fires when every
    attempt fails validation - simulated bad JSON, then a disallowed category.
    Distinct from a ticket where the model legitimately self-selects
    'uncategorized' (see e02 in tickets.py) - see taxonomy.json notes.uncategorized."""
    resolved = resolve(["this is not json", '{"category": "bogus", "priority": "High", "reasoning": "x"}'])
    assert resolved.used_fallback, "expected fallback to fire on two invalid attempts"
    assert resolved.result == FALLBACK_RESULT
    return resolved


def print_report(outcomes):
    passed = sum(1 for o in outcomes if o.passed)
    total = len(outcomes)
    print(f"{passed}/{total} tickets passed\n")
    for o in outcomes:
        status = "PASS" if o.passed else "FAIL"
        print(f"[{status}] {o.ticket_id}  ({o.latency_s * 1000:.1f} ms)")
        if o.validation_errors:
            print(f"    validation errors: {o.validation_errors}")
        for note in o.notes:
            print(f"    {note}")

        if o.got:
            print(f"    reasoning: {o.got['reasoning']!r}")

    latencies = [o.latency_s for o in outcomes]
    if latencies:
        print(
            f"\nlatency: min={min(latencies) * 1000:.1f}ms "
            f"max={max(latencies) * 1000:.1f}ms "
            f"mean={sum(latencies) / len(latencies) * 1000:.1f}ms"
        )


if __name__ == "__main__":
    from router import route_ticket


    print("=== Fallback / malformed-response check ===")
    test_fallback_on_malformed_response()
    print("OK: resolve() fell back to the safe default on malformed input.\n")

    print("=== Ticket harness run (mock router - NOT the real prompt) ===")
    outcomes = run_harness(route_ticket)
    print_report(outcomes)
    
