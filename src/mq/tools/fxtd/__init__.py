"""FixMe ToDo Module Configuration."""

from pathlib import Path

from mq.tools.base import AbstractToolConfiguration
from mq.tools.fxtd.models import Fxtd

COLORS: dict = dict(positive="red", negative="green", neutral="white")


DEFAULT_SCORING = {
    "fxtd.by_type_per_kloc": {
        "reverse": False,  # Lower is better...
        "thresholds": [
            {"max": 2, "grade": "A", "color": "#22c55e"},
            {"max": 5, "grade": "B", "color": "#84cc16"},
            {"max": 10, "grade": "C", "color": "#eab308"},
            {"max": 20, "grade": "D", "color": "#f97316"},
            {"max": "inf", "grade": "F", "color": "#ef4444"},
        ],
    },
    "fxtd.composite_weighted_per_kloc": {
        "reverse": False,  # Lower is better...
        "thresholds": [
            {"max": 2, "grade": "A", "color": "#22c55e"},
            {"max": 5, "grade": "B", "color": "#84cc16"},
            {"max": 10, "grade": "C", "color": "#eab308"},
            {"max": 20, "grade": "D", "color": "#f97316"},
            {"max": "inf", "grade": "F", "color": "#ef4444"},
        ],
    },
}


class Configuration(AbstractToolConfiguration):
    """Configure semantics associated with using the tool."""

    def __init__(self):
        """..."""
        super(Configuration, self).__init__(
            module_name="fxtd",
            models=dict(fxtd=Fxtd),
            results_required=False,  # In this case,  Scans without data ARE valid!
        )

    def get_ingest_command(self, relative: str = None, absolute: str = None, analysis: str = None) -> list[str]:
        """Return the command sent to subprocess to directly perform the scan operation."""
        script_dir = Path(__file__).parent
        fxtd_script = script_dir / "fxtd.sh"
        assert fxtd_script.exists(), f"Sorry, we expected to find 'fxtd.sh' at {script_dir}!"
        return [str(fxtd_script), str(absolute)]
