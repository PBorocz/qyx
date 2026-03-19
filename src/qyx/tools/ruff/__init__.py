"""Ruff Module Configuration."""

import gzip
import json
from pathlib import Path

from qyx.tools._models_ import ToolDimension, ToolType
from qyx.tools.ruff.models import Ruff, RuffMessage, RuffUrl

RUFF_RULES = None  # Hold as a cache after first read


DIMENSIONS = [
    ToolDimension("ruff", "Astral code linter", (Ruff, RuffMessage, RuffUrl)),
]


class Configuration(ToolType):
    """Configure semantics associated with using the ruff tool."""

    def __init__(self, module: str):
        """..."""
        super(Configuration, self).__init__(
            module=module,
            name="ruff",
            description="Astral code linter",
            dimensions=DIMENSIONS,
            results_required=False,  # In this case,  Ruff Scans without data ARE valid!
        )


def get_ruff_rule_name(rule_code: str) -> dict:
    """Lookup the description of the ruff rule name for a rule code."""
    global RUFF_RULES

    # Load in rule definitions if we haven't already..
    if not RUFF_RULES:
        rules_path: Path = "src/qyx/tools/ruff/data/ruff_rules.json.gz"
        with gzip.open(rules_path, "rt", encoding="utf-8") as f:
            RUFF_RULES = json.load(f)

    for rule in RUFF_RULES:
        if rule.get("code").lower() == rule_code.lower():
            return rule["name"]

    return "-Unknown Rule: {rule_code}-"
