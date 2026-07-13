import json
from pathlib import Path

_TAXONOMY_PATH = Path(__file__).parent / "taxonomy.json"

with open(_TAXONOMY_PATH) as f:
    _DATA = json.load(f)

CATEGORIES = _DATA["categories"]
PRIORITIES = _DATA["priorities"]

VALID_CATEGORY_IDS = {c["id"] for c in CATEGORIES}
VALID_PRIORITIES = set(PRIORITIES)
CATEGORY_TO_TEAM = {c["id"]: c["team"] for c in CATEGORIES}
VALID_TEAMS = set(CATEGORY_TO_TEAM.values())


def team_for_category(category: str) -> str:
    return CATEGORY_TO_TEAM[category]
