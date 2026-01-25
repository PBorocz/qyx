"""Ruff Module Configuration."""

import gzip
import json
from pathlib import Path

from mq.tools.base import ToolConfig
from mq.tools.ruff.models import Ruff

RUFF_RULES = None  # Hold as a cache after first read
COLORS: dict = dict(positive="red", negative="green", neutral="white")


class Configuration(ToolConfig):
    """Configure semantics associated with using the ruff tool."""

    def __init__(self):
        """..."""
        super(Configuration, self).__init__(
            module_name="ruff",
            models=dict(ruff=Ruff),
            results_required=False,  # In this case,  Ruff Scans without data ARE valid!
        )

    def get_ingest_command(self, relative: str = None, absolute: str = None, analysis: str = None) -> list[str]:
        """Return the command sent to subprocess to directly perform a Ruff operation."""
        return [
            "ruff",
            "check",
            "--exit-zero",
            "--output-format=json",
            absolute,
        ]


def get_ruff_rule_name(rule_code: str) -> dict:
    """Lookup the description of the ruff rule name for a rule code."""
    global RUFF_RULES

    # Load in rule definitions if we haven't already..
    if not RUFF_RULES:
        rules_path: Path = "src/mq/tools/ruff/data/ruff_rules.json.gz"
        with gzip.open(rules_path, "rt", encoding="utf-8") as f:
            RUFF_RULES = json.load(f)

    for rule in RUFF_RULES:
        if rule.get("code").lower() == rule_code.lower():
            return rule["name"]

    return "-Unknown Rule: {rule_code}-"
