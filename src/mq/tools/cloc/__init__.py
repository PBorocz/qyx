"""Cloc Module Configuration."""

from mq.tools.base import AbstractToolConfiguration
from mq.tools.cloc.models import Cloc

DEFAULT_SCORING = {
    "cloc.code_density": {
        "thresholds": [
            {"min": 0, "max": 10, "grade": "B", "color": "#84cc16"},
            {"min": 10, "max": 60, "grade": "A", "color": "#22c55e"},
            {"min": 60, "max": 85, "grade": "C", "color": "#eab308"},
            {"min": 85, "max": float("inf"), "grade": "F", "color": "#ef4444"},
        ],
    },
    "cloc.comment_ratio": {
        # Score falls in range [min, max) - higher is better
        "thresholds": [
            {"min": 20, "max": float("inf"), "grade": "A", "color": "#22c55e"},
            {"min": 15, "max": 20, "grade": "B", "color": "#84cc16"},
            {"min": 10, "max": 15, "grade": "C", "color": "#eab308"},
            {"min": 5, "max": 10, "grade": "D", "color": "#f97316"},
            {"min": 0, "max": 5, "grade": "F", "color": "#ef4444"},
        ],
    },
    "cloc.avg_lines_per_file": {
        # Score falls in range [min, max) - higher is (usually) better
        "thresholds": [
            {"min": 0, "max": 200, "grade": "A", "color": "#22c55e"},
            {"min": 200, "max": 300, "grade": "B", "color": "#84cc16"},
            {"min": 300, "max": 400, "grade": "C", "color": "#eab308"},
            {"min": 400, "max": 600, "grade": "D", "color": "#f97316"},
            {"min": 600, "max": float("inf"), "grade": "F", "color": "#ef4444"},
        ],
    },
}


class Configuration(AbstractToolConfiguration):
    """Configure semantics associated with using the cloc tool."""

    def __init__(self):
        """..."""
        super(Configuration, self).__init__(
            module_name="cloc",
            models=dict(cloc=Cloc),
        )

    def get_ingest_command(self, relative: str = None, absolute: str = None, analysis: str = None) -> list[str]:
        """Return the command sent to subprocess to directly perform a CLOC operation."""
        return [
            "cloc",
            "--include-lang=Python",
            "--by-file",
            "--json",
            "--exclude-dir=.venv",
            absolute,
        ]
