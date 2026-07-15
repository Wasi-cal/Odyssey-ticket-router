import json

from pydantic import BaseModel, Field

from taxonomy import VALID_CATEGORY_IDS, VALID_PRIORITIES, team_for_category

REQUIRED_FIELDS = ("category", "priority", "reasoning", "title")

FALLBACK_RESULT = {
    "category": "uncategorized",
    "priority": "High",
    "team": team_for_category("uncategorized"),
    "reasoning": "flagged for human review",
    "title": "Flagged for manual review",
}


class ValidationResult(BaseModel):
    is_valid: bool
    errors: list
    result: dict | None = None


def validate(raw_response) -> ValidationResult:
    """Deterministic checks only: JSON parses, category/priority are in the
    taxonomy's allowed lists, reasoning is non-empty. 'team' is not requested
    from the model - it's derived from category via the taxonomy mapping."""
    if isinstance(raw_response, str):
        try:
            data = json.loads(raw_response)
        except json.JSONDecodeError as e:
            return ValidationResult(is_valid=False, errors=[f"not valid JSON: {e}"])
    elif isinstance(raw_response, dict):
        data = raw_response
    else:
        return ValidationResult(
            is_valid=False, errors=[f"unexpected response type: {type(raw_response).__name__}"]
        )

    if not isinstance(data, dict):
        return ValidationResult(is_valid=False, errors=["parsed JSON is not an object"])

    errors = [f"missing field: {name}" for name in REQUIRED_FIELDS if name not in data]
    if errors:
        return ValidationResult(is_valid=False, errors=errors)

    category = data["category"]
    priority = data["priority"]
    reasoning = data["reasoning"]
    title = data["title"]   

    if category not in VALID_CATEGORY_IDS:
        errors.append(f"invalid category: {category!r}")
    if priority not in VALID_PRIORITIES:
        errors.append(f"invalid priority: {priority!r}")
    if not isinstance(reasoning, str) or not reasoning.strip():
        errors.append("reasoning is empty")

    if errors:
        return ValidationResult(is_valid=False, errors=errors)

    result = {
        "category": category,
        "priority": priority,
        "team": team_for_category(category),
        "reasoning": reasoning,
        "title": title,  
    }
    return ValidationResult(is_valid=True, errors=[], result=result)


class ResolvedResult(BaseModel):
    result: dict
    used_fallback: bool
    attempts_tried: int
    errors: list = Field(default_factory=list)


def resolve(attempts) -> ResolvedResult:
    """Try each raw response in order (e.g. [first_call, retry_call]); return the
    first one that validates, or the safe fallback if none do. LLM-agnostic -
    callers pass whatever raw responses they got, real or simulated."""
    last_errors = []
    for i, raw in enumerate(attempts, start=1):
        outcome = validate(raw)
        if outcome.is_valid:
            return ResolvedResult(result=outcome.result, used_fallback=False, attempts_tried=i)
        last_errors = outcome.errors
    return ResolvedResult(
        result=dict(FALLBACK_RESULT), used_fallback=True, attempts_tried=len(attempts), errors=last_errors
    )
