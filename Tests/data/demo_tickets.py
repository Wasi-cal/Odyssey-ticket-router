import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "taxonomy"))
sys.path.insert(0, str(_ROOT / "Tests"))

from tickets import TestTicket

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
        "d01",
        "My invoice this month is $40 higher than my usual plan cost, and I don't see any "
        "add-ons or usage overage listed. Can someone explain the charge?",
        "billing", frozenset({"Medium"}),
    ),
    TestTicket(
        "d02",
        "I upgraded to the Team plan last week but I'm still being billed at the old Starter "
        "rate. Can you correct this before my next invoice?",
        "billing", frozenset({"Medium"}),
    ),
    TestTicket(
        "d03",
        "Our payment method on file expired and I can't find where to update it in the settings page.",
        "billing", frozenset({"Medium", "High"}),
    ),

    # api_integration
    TestTicket(
        "d04",
        "We're seeing intermittent 500 errors from the /v1/embeddings endpoint for about "
        "1 in 20 requests over the last hour.",
        "api_integration", frozenset({"High"}),
    ),
    TestTicket(
        "d05",
        "Is there a way to increase our organization's concurrent request limit? We're hitting "
        "429s during peak traffic.",
        "api_integration", frozenset({"Medium", "High"}),
    ),
    TestTicket(
        "d06",
        "How do I paginate through results when calling the /v1/list-runs endpoint from the "
        "Python SDK?",
        "general_inquiry", frozenset({"Low"}),
        tags=["edge_ambiguous"],
    ),

    # account_access
    TestTicket(
        "d07",
        "I need to remove a former employee's access to our workspace immediately, they left "
        "the company yesterday.",
        "account_access", frozenset({"High"}),
    ),
    TestTicket(
        "d08",
        "Can I merge two workspaces under one account? We accidentally created a duplicate org.",
        "account_access", frozenset({"Low", "Medium"}),
    ),
    TestTicket(
        "d09",
        "None of my team members can see the new project I created, even though I gave them "
        "'Editor' access.",
        "account_access", frozenset({"Medium"}),
    ),

    # general_inquiry
    TestTicket(
        "d10",
        "Do you have a comparison of your Pro vs Enterprise plans somewhere?",
        "general_inquiry", frozenset({"Low"}),
    ),
    TestTicket(
        "d11",
        "What programming languages do your official SDKs support?",
        "general_inquiry", frozenset({"Low"}),
    ),
    TestTicket(
        "d12",
        "Is there a changelog or release notes page where I can see what's new each month?",
        "general_inquiry", frozenset({"Low"}),
    ),

    # outage
    TestTicket(
        "d13",
        "Our production integration has been down for 15 minutes, every API call returns a 503.",
        "outage", frozenset({"High"}),
    ),
    TestTicket(
        "d14",
        "This is the SECOND outage this week and nobody from your team has posted a single "
        "status update. We are losing customers every minute this stays down - completely unacceptable.",
        "outage", frozenset({"High"}),
        tags=["edge_angry_tone"],
    ),

    # product_bug
    TestTicket(
        "d15",
        "The 'export to PDF' button on the reports page does nothing when I click it, no "
        "error, no download.",
        "product_bug", frozenset({"Medium"}),
    ),
    TestTicket(
        "d16",
        "Search results on the knowledge base page are sorted randomly instead of by relevance.",
        "product_bug", frozenset({"Low", "Medium"}),
    ),

    # feature_request
    TestTicket(
        "d17",
        "Would love the ability to set custom alert thresholds for usage instead of just the "
        "default 80%/100% warnings.",
        "feature_request", frozenset({"Low"}),
    ),
    TestTicket(
        "d18",
        "Any plans to support SSO login via Okta? That would help us roll this out company-wide.",
        "feature_request", frozenset({"Low"}),
    ),

    # abuse_policy
    TestTicket(
        "d19",
        "Someone outside our org is using a leaked API key from our account to send large "
        "volumes of requests - flagging this as a security concern.",
        "abuse_policy", frozenset({"High"}),
    ),

    # vague / short (uncategorized edge case)
    TestTicket(
        "d20",
        "nothing works",
        "uncategorized", frozenset({"Medium"}),
        tags=["edge_short_message"],
    ),
]


if __name__ == "__main__":
    from router import classify
    from harness import run_harness, print_report

    outcomes = run_harness(lambda text: classify(text).result, tickets=DEMO_TICKETS)
    print_report(outcomes)
