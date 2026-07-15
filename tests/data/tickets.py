from pydantic import BaseModel, Field


class TestTicket(BaseModel):
    id: str
    text: str
    expected_category: str | None = None
    expected_priorities: frozenset | None = None
    tags: list = Field(default_factory=list)


ALL_TICKETS = [
    TestTicket(
        id="t01",
        text="I was charged twice for my Pro subscription this month. Please refund the duplicate charge.",
        expected_category="billing", expected_priorities=frozenset({"Medium"}),
    ),
    TestTicket(
        id="t02",
        text="Can I switch from the monthly to the annual plan mid-cycle, and will I get prorated credit?",
        expected_category="billing", expected_priorities=frozenset({"Low", "Medium"}),
    ),
    TestTicket(
        id="t03",
        text="Our webhook endpoint stopped receiving events after your API update yesterday. "
        "This is blocking our production pipeline.",
        expected_category="api_integration", expected_priorities=frozenset({"High"}),
    ),
    TestTicket(
        id="t04",
        text="What's the rate limit for the /v1/chat/completions endpoint on the free tier?",
        expected_category="api_integration", expected_priorities=frozenset({"Low"}),
    ),
    TestTicket(
        id="t05",
        text="I've been locked out of my account after 3 failed 2FA attempts and need it restored ASAP, "
        "my whole team can't access anything.",
        expected_category="account_access", expected_priorities=frozenset({"High"}),
    ),
    TestTicket(
        id="t06",
        text="How do I add a teammate as an admin on our workspace?",
        expected_category="account_access", expected_priorities=frozenset({"Low", "Medium"}),
    ),
    TestTicket(
        id="t07",
        text="The dashboard chart on the analytics page shows the wrong date range no matter what filter I pick.",
        expected_category="product_bug", expected_priorities=frozenset({"Medium"}),
    ),
    TestTicket(
        id="t08",
        text="Nothing is loading on your end, your status page shows all green but every request from us "
        "is timing out right now.",
        expected_category="outage", expected_priorities=frozenset({"High"}),
    ),
    TestTicket(
        id="t09",
        text="It would be great if we could export usage reports as CSV instead of just PDF.",
        expected_category="feature_request", expected_priorities=frozenset({"Low"}),
    ),
    TestTicket(
        id="t10",
        text="Do you have documentation on how streaming responses work with the SDK?",
        expected_category="general_inquiry", expected_priorities=frozenset({"Low"}),
    ),
    TestTicket(
        id="t11",
        text="I want to report that a user in our workspace is using the API to generate content "
        "that violates your usage policy.",
        expected_category="abuse_policy", expected_priorities=frozenset({"Medium", "High"}),
    ),
    TestTicket(
        id="t12",
        text="I think I found a way to bypass the content moderation filter, wanted to responsibly disclose this.",
        expected_category="abuse_policy", expected_priorities=frozenset({"High"}),
    ),
    TestTicket(
        id="e01",
        text="This is ABSOLUTELY RIDICULOUS. I've been billed for a plan I cancelled three months ago "
        "and NO ONE has responded to my last 4 emails. Fix this NOW or I'm cancelling everything "
        "and telling everyone how bad your support is.",
        expected_category="billing", expected_priorities=frozenset({"High"}),
        tags=["edge_angry_tone"],
    ),
    TestTicket(
        id="e02",
        text="it's broken",
        expected_category="uncategorized", expected_priorities=frozenset({"Medium"}),
        tags=["edge_short_message"],
    ),
    TestTicket(
        id="e03",
        text="Getting weird results back from the API when I call it through the SDK, not sure if it's "
        "a bug on your end or something with my webhook setup.",
        expected_category="api_integration", expected_priorities=frozenset({"Medium"}),
        tags=["edge_ambiguous"],
    ),
]
