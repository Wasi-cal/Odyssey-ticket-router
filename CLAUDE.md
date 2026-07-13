# Smart Ticket Router — project brief

## Mission

Build a Smart Ticket Router: reads a support ticket message and outputs structured JSON with `category`, `priority` (High/Medium/Low), assigned `team`, and a one-line `reasoning`.

Domain: an AI startup's customer support desk (product support, billing, API/integration issues, account access, feature requests, outages, etc.).

## Deliverables (from the assignment)

1. Prompts that consistently return valid structured JSON.
2. Handling for 3 edge cases: angry tone, very short message, ambiguous ticket.
3. A simple interface (web form, CLI, or ERP screen) to test it.
4. Before/after: manual routing time vs AI routing time.
5. Demo of 20 sample tickets.

## Architecture (already agreed)

```
Interface (ticket text submitted)
  -> Router service (builds prompt, calls LLM)
  -> Validator (checks JSON validity, category/team/priority against fixed lists, non-empty reasoning)
  -> branches:
       - valid   -> Structured JSON output {category, priority, team, reasoning}
       - invalid -> retry once, then safe fallback default
                    (e.g. Uncategorized / Medium / Tier 1 / "flagged for human review")
  -> both paths converge back to Interface (result displayed)
```

Supporting components (not in the main flow, but feed it):

- **Taxonomy config** — the fixed lists of categories, teams, and priority levels. Single source of truth used by both the prompt builder and the validator. NOT YET DEFINED — this is the immediate next step.
- **Test harness** — a fixed batch of tickets (including the 3 edge cases) paired with expected outcomes. Used to score every prompt iteration objectively instead of eyeballing results, and to log AI response latency for the before/after timing deliverable.

## Build order (in progress)

1. **Define taxonomy and JSON schema — START HERE.** Propose a finished list of categories, the team each category routes to, and priority level definitions for an AI startup support desk. Ask me clarifying questions if genuinely needed, then propose the taxonomy for review before writing any code.
2. Build the test harness (fixed tickets + expected outcomes + validity checks: parses as JSON, category/priority/team are in the allowed lists, reasoning is non-empty).
3. Draft a v1 system/user prompt — deliberately minimal/naive, not pre-hardened against edge cases. Run it against the harness and see what breaks.
4. Iterate the prompt against the harness, patching one edge case at a time (angry tone -> short message -> ambiguous ticket), rerunning the full harness after each patch to catch regressions. Keep old prompt versions around (v1, v2, v3...) for the before/after story.
5. Add the deterministic validation + retry-then-fallback layer. This is plain code (JSON parse, enum membership checks, non-empty checks) — NOT a second AI model validating the first.
6. Wrap it all into a single reusable router function, used by both the harness and the interface.
7. Build the interface (web form or CLI) as a thin wrapper around that function.
8. Time manual triage vs AI routing on the same set of tickets (stopwatch for manual, logged latency for AI).
9. Prepare the final 20-ticket demo set (mix of normal + edge-case tickets) and package results.

## Key decisions already made

- **Schema uses single values, not lists.** `{category: string, priority: "High"|"Medium"|"Low", team: string, reasoning: string}`. A router must commit to one category/team — returning multiple tags defeats the purpose of routing.
- **Validation is deterministic, not another AI model.** JSON parse + enum membership + non-empty reasoning check. Using a second LLM to validate the first just compounds unreliability instead of fixing it.
- **Model choice:** don't reach for frontier/reasoning models here — this is a well-defined, repetitive classification task. A small, fast, cheap model with native structured-output/JSON-schema enforcement is the right fit (e.g. Claude Haiku 4.5, GPT-5.4 mini/nano, Gemini 3.1 Flash-Lite, as of mid-2026 pricing/capability). Pick whichever is easiest to provision; accuracy differences between them on a fixed taxonomy are marginal.
- **Edge case handling:**
  - Angry tone should raise priority, not change category (sentiment ≠ category).
  - Very short/low-info messages should get a low-confidence default (e.g. flagged for human review) rather than a confidently wrong guess.
  - Ambiguous tickets need an explicit tie-break rule, not a list of multiple categories.
- **Prompt structure:** system prompt carries the stable contract (role, taxonomy, output schema, format rules); user prompt carries only the raw ticket text. Iterate by testing against the fixed harness, not by eyeballing individual outputs.

## Working notes

I'll paste your outputs (taxonomy proposals, prompt drafts, test results) back into the original planning conversation for review, or we can just continue directly here — either works.
