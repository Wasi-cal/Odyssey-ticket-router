from dataclasses import dataclass, field


@dataclass
class TestTicket:
    id: str
    text: str
    expected_category: str | None = None
    expected_priorities: frozenset | None = None
    tags: list = field(default_factory=list)


ALL_TICKETS = [
    TestTicket(
        "t01",
        "I was charged twice for my Pro subscription this month. Please refund the duplicate charge.",
        "billing", frozenset({"Medium"}),
    ),
    TestTicket(
        "t02",
        "Can I switch from the monthly to the annual plan mid-cycle, and will I get prorated credit?",
        "billing", frozenset({"Low", "Medium"}),
    ),
    TestTicket(
        "t03",
        "Our webhook endpoint stopped receiving events after your API update yesterday. "
        "This is blocking our production pipeline.",
        "api_integration", frozenset({"High"}),
    ),
    TestTicket(
        "t04",
        "What's the rate limit for the /v1/chat/completions endpoint on the free tier?",
        "api_integration", frozenset({"Low"}),
    ),
    TestTicket(
        "t05",
        "I've been locked out of my account after 3 failed 2FA attempts and need it restored ASAP, "
        "my whole team can't access anything.",
        "account_access", frozenset({"High"}),
    ),
    TestTicket(
        "t06",
        "How do I add a teammate as an admin on our workspace?",
        "account_access", frozenset({"Low", "Medium"}),
    ),
    TestTicket(
        "t07",
        "The dashboard chart on the analytics page shows the wrong date range no matter what filter I pick.",
        "product_bug", frozenset({"Medium"}),
    ),
    TestTicket(
        "t08",
        "Nothing is loading on your end, your status page shows all green but every request from us "
        "is timing out right now.",
        "outage", frozenset({"High"}),
    ),
    TestTicket(
        "t09",
        "It would be great if we could export usage reports as CSV instead of just PDF.",
        "feature_request", frozenset({"Low"}),
    ),
    TestTicket(
        "t10",
        "Do you have documentation on how streaming responses work with the SDK?",
        "general_inquiry", frozenset({"Low"}),
    ),
    TestTicket(
        "t11",
        "I want to report that a user in our workspace is using the API to generate content "
        "that violates your usage policy.",
        "abuse_policy", frozenset({"Medium", "High"}),
    ),
    TestTicket(
        "t12",
        "I think I found a way to bypass the content moderation filter, wanted to responsibly disclose this.",
        "abuse_policy", frozenset({"High"}),
    ),
    TestTicket(
        "e01",
        "This is ABSOLUTELY RIDICULOUS. I've been billed for a plan I cancelled three months ago "
        "and NO ONE has responded to my last 4 emails. Fix this NOW or I'm cancelling everything "
        "and telling everyone how bad your support is.",
        "billing", frozenset({"High"}),
        tags=["edge_angry_tone"],
    ),
    TestTicket(
        "e02",
        "it's broken",
        "uncategorized", frozenset({"Medium"}),
        tags=["edge_short_message"],
    ),
    TestTicket(
        "e03",
        "Getting weird results back from the API when I call it through the SDK, not sure if it's "
        "a bug on your end or something with my webhook setup.",
        "api_integration", frozenset({"Medium"}),
        tags=["edge_ambiguous"],
    ),
]
