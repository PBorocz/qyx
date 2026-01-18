"""Ruff Module Configuration."""

import gzip
import json
from pathlib import Path

from mq.tools.base import AbstractToolConfiguration
from mq.tools.ruff.models import Ruff

RUFF_RULES = None  # Hold as a cache after first read
COLORS: dict = dict(positive="red", negative="green", neutral="white")


DEFAULT_SCORING = {
    "ruff.violations_per_kloc": {
        "thresholds": [
            {"min": 0, "max": 5, "grade": "A", "color": "#22c55e"},
            {"min": 5, "max": 10, "grade": "B", "color": "#84cc16"},
            {"min": 10, "max": 20, "grade": "C", "color": "#eab308"},
            {"min": 20, "max": 40, "grade": "D", "color": "#f97316"},
            {"min": 40, "max": "inf", "grade": "F", "color": "#ef4444"},
        ],
    },
    "ruff.weighted_violations_per_kloc": {
        "thresholds": [
            {"min": 0, "max": 10, "grade": "A", "color": "#22c55e"},
            {"min": 10, "max": 25, "grade": "B", "color": "#84cc16"},
            {"min": 25, "max": 50, "grade": "C", "color": "#eab308"},
            {"min": 50, "max": 100, "grade": "D", "color": "#f97316"},
            {"min": 100, "max": "inf", "grade": "F", "color": "#ef4444"},
        ],
    },
}


class Configuration(AbstractToolConfiguration):
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
