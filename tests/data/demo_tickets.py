import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "src" / "taxonomy"))
sys.path.insert(0, str(_ROOT / "Tests"))

from backend.Tests.data.tickets import TestTicket

# Fresh 20-ticket demo set - none of these are reused from tickets.py (the
# regression set the prompt was tuned against). Point is to show the prompt
# generalizes to new phrasing, not just known-good cases.
#
# Mix: 3 each for the categories that had real confusion during iteration
# (billing, api_integration, account_access, general_inquiry), 2 each for the
# rest, 1 abuse_policy, plus edge cases: a new angry-tone ticket (tagged onto
# an outage instead of billing this time, to prove anger->priority generalizes
# across categories), a new vague/short ticket, and an ambiguous SDK/API
# how-to ticket (d06) that deliberately sits on the same
# conceptual-vs-account-specific line the v1 prompt got wrong on t04/t06 -
# this one tests the opposite failure mode: does the fix now overcorrect and
# tag a purely conceptual SDK question as api_integration?

DEMO_TICKETS = [
    # billing
    TestTicket(
        id="d01",
        text="My invoice this month is $40 higher than my usual plan cost, and I don't see any "
        "add-ons or usage overage listed. Can someone explain the charge?",
        expected_category="billing", expected_priorities=frozenset({"Medium"}),
    ),
    TestTicket(
        id="d02",
        text="I upgraded to the Team plan last week but I'm still being billed at the old Starter "
        "rate. Can you correct this before my next invoice?",
        expected_category="billing", expected_priorities=frozenset({"Medium"}),
    ),
    TestTicket(
        id="d03",
        text="Our payment method on file expired and I can't find where to update it in the settings page.",
        expected_category="billing", expected_priorities=frozenset({"Medium", "High"}),
    ),

    # api_integration
    TestTicket(
        id="d04",
        text="We're seeing intermittent 500 errors from the /v1/embeddings endpoint for about "
        "1 in 20 requests over the last hour.",
        expected_category="api_integration", expected_priorities=frozenset({"High"}),
    ),
    TestTicket(
        id="d05",
        text="Is there a way to increase our organization's concurrent request limit? We're hitting "
        "429s during peak traffic.",
        expected_category="api_integration", expected_priorities=frozenset({"Medium", "High"}),
    ),
    TestTicket(
        id="d06",
        text="How do I paginate through results when calling the /v1/list-runs endpoint from the "
        "Python SDK?",
        expected_category="general_inquiry", expected_priorities=frozenset({"Low"}),
        tags=["edge_ambiguous"],
    ),

    # account_access
    TestTicket(
        id="d07",
        text="I need to remove a former employee's access to our workspace immediately, they left "
        "the company yesterday.",
        expected_category="account_access", expected_priorities=frozenset({"High"}),
    ),
    TestTicket(
        id="d08",
        text="Can I merge two workspaces under one account? We accidentally created a duplicate org.",
        expected_category="account_access", expected_priorities=frozenset({"Low", "Medium"}),
    ),
    TestTicket(
        id="d09",
        text="None of my team members can see the new project I created, even though I gave them "
        "'Editor' access.",
        expected_category="account_access", expected_priorities=frozenset({"Medium"}),
    ),

    # general_inquiry
    TestTicket(
        id="d10",
        text="Do you have a comparison of your Pro vs Enterprise plans somewhere?",
        expected_category="general_inquiry", expected_priorities=frozenset({"Low"}),
    ),
    TestTicket(
        id="d11",
        text="What programming languages do your official SDKs support?",
        expected_category="general_inquiry", expected_priorities=frozenset({"Low"}),
    ),
    TestTicket(
        id="d12",
        text="Is there a changelog or release notes page where I can see what's new each month?",
        expected_category="general_inquiry", expected_priorities=frozenset({"Low"}),
    ),

    # outage
    TestTicket(
        id="d13",
        text="Our production integration has been down for 15 minutes, every API call returns a 503.",
        expected_category="outage", expected_priorities=frozenset({"High"}),
    ),
    TestTicket(
        id="d14",
        text="This is the SECOND outage this week and nobody from your team has posted a single "
        "status update. We are losing customers every minute this stays down - completely unacceptable.",
        expected_category="outage", expected_priorities=frozenset({"High"}),
        tags=["edge_angry_tone"],
    ),

    # product_bug
    TestTicket(
        id="d15",
        text="The 'export to PDF' button on the reports page does nothing when I click it, no "
        "error, no download.",
        expected_category="product_bug", expected_priorities=frozenset({"Medium"}),
    ),
    TestTicket(
        id="d16",
        text="Search results on the knowledge base page are sorted randomly instead of by relevance.",
        expected_category="product_bug", expected_priorities=frozenset({"Low", "Medium"}),
    ),

    # feature_request
    TestTicket(
        id="d17",
        text="Would love the ability to set custom alert thresholds for usage instead of just the "
        "default 80%/100% warnings.",
        expected_category="feature_request", expected_priorities=frozenset({"Low"}),
    ),
    TestTicket(
        id="d18",
        text="Any plans to support SSO login via Okta? That would help us roll this out company-wide.",
        expected_category="feature_request", expected_priorities=frozenset({"Low"}),
    ),

    # abuse_policy
    TestTicket(
        id="d19",
        text="Someone outside our org is using a leaked API key from our account to send large "
        "volumes of requests - flagging this as a security concern.",
        expected_category="abuse_policy", expected_priorities=frozenset({"High"}),
    ),

    # vague / short (uncategorized edge case)
    TestTicket(
        id="d20",
        text="nothing works",
        expected_category="uncategorized", expected_priorities=frozenset({"Medium"}),
        tags=["edge_short_message"],
    ),
]


if __name__ == "__main__":
    from router import classify
    from backend.Tests.harness import run_harness, print_report

    outcomes = run_harness(lambda text: classify(text).result, tickets=DEMO_TICKETS)
    print_report(outcomes)
