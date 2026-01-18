"""Radon Module Configuration."""

import types
from typing import Callable

from mq.tools.base import AbstractToolConfiguration
from mq.tools.radon.models import RadonCc, RadonHal, RadonHalFunction, RadonMi, RadonRaw

COLORS: dict = dict(positive="red", negative="green", neutral="white")


DEFAULT_SCORING = {
    "radon.cc.classes": {
        "thresholds": [
            {"min": 0, "max": 20, "grade": "A", "color": "#22c55e"},
            {"min": 20, "max": 40, "grade": "B", "color": "#84cc16"},
            {"min": 40, "max": 80, "grade": "C", "color": "#eab308"},
            {"min": 80, "max": 150, "grade": "D", "color": "#f97316"},
            {"min": 150, "max": "inf", "grade": "F", "color": "#ef4444"},
        ],
    },
    "radon.cc.callables": {
        "thresholds": [
            {"min": 0, "max": 20, "grade": "A", "color": "#22c55e"},
            {"min": 20, "max": 40, "grade": "B", "color": "#84cc16"},
            {"min": 40, "max": 80, "grade": "C", "color": "#eab308"},
            {"min": 80, "max": 150, "grade": "D", "color": "#f97316"},
            {"min": 150, "max": "inf", "grade": "F", "color": "#ef4444"},
        ],
    },
    "radon.mi.mean": {
        "thresholds": [
            {"min": 85, "max": "inf", "grade": "A", "color": "#22c55e"},
            {"min": 75, "max": 85, "grade": "B", "color": "#84cc16"},
            {"min": 65, "max": 75, "grade": "C", "color": "#eab308"},
            {"min": 50, "max": 65, "grade": "D", "color": "#f97316"},
            {"min": "inf", "max": 50, "grade": "F", "color": "#ef4444"},
        ],
    },
    "radon.hal.composite": {
        "thresholds": [
            {"min": 80, "max": "inf", "grade": "A", "color": "#22c55e"},
            {"min": 70, "max": 80, "grade": "B", "color": "#84cc16"},
            {"min": 60, "max": 70, "grade": "C", "color": "#eab308"},
            {"min": 50, "max": 60, "grade": "D", "color": "#f97316"},
            {"min": "inf", "max": 50, "grade": "F", "color": "#ef4444"},
        ],
    },
    "radon.hal.bugs": {
        "thresholds": [
            {"min": 0.0, "max": 0.1, "grade": "A", "color": "#22c55e"},
            {"min": 0.1, "max": 0.3, "grade": "B", "color": "#84cc16"},
            {"min": 0.3, "max": 0.6, "grade": "C", "color": "#eab308"},
            {"min": 0.6, "max": 1.0, "grade": "D", "color": "#f97316"},
            {"min": 1.0, "max": "inf", "grade": "F", "color": "#ef4444"},
        ],
    },
    "radon.hal.effort": {
        "thresholds": [
            {"min": 0, "max": 100, "grade": "A", "color": "#22c55e"},
            {"min": 100, "max": 300, "grade": "B", "color": "#84cc16"},
            {"min": 300, "max": 600, "grade": "C", "color": "#eab308"},
            {"min": 600, "max": 1000, "grade": "D", "color": "#f97316"},
            {"min": 1000, "max": "inf", "grade": "F", "color": "#ef4444"},
        ],
    },
    "radon.hal.difficulty": {
        "thresholds": [
            {"min": 0, "max": 5, "grade": "A", "color": "#22c55e"},
            {"min": 5, "max": 10, "grade": "B", "color": "#84cc16"},
            {"min": 10, "max": 20, "grade": "C", "color": "#eab308"},
            {"min": 20, "max": 40, "grade": "D", "color": "#f97316"},
            {"min": 40, "max": "inf", "grade": "F", "color": "#ef4444"},
        ],
    },
}


class Configuration(AbstractToolConfiguration):
    """Configure semantics associated with using the various Radon tools."""

    def __init__(self):
        """..."""
        super(Configuration, self).__init__(
            module_name="radon",
            models=dict(
                cc=RadonCc,
                hal=RadonHal,
                _hal=RadonHalFunction,
                mi=RadonMi,
                raw=RadonRaw,
            ),
        )

    def get_ingest_command(self, relative: str = None, absolute: str = None, analysis: str = None) -> list[str]:
        """Return the command sent to subprocess to directly perform an ingest operation."""
        assert analysis, "Sorry, we need a sub_module here!"
        return [
            "uvx",
            "radon",
            analysis,
            "--json",
            absolute,
        ]

    def get_ingest_method(self, analysis: str) -> Callable:
        """Return the ingest method to parse & save this Radon analysis's JSON output."""
        py_ingest: types.ModuleType = self.import_component("ingest")  # eg. .../<module>/ingest.py
        return getattr(py_ingest, f"ingest_{analysis.lower()}")  # eg. ingest_cc()
