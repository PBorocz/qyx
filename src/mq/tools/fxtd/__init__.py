"""FixMe ToDo Module Configuration."""

from pathlib import Path

from mq.tools.base import ToolConfig
from mq.tools.fxtd.models import Fxtd

COLORS: dict = dict(positive="red", negative="green", neutral="white")


class Configuration(ToolConfig):
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
        fxtd_script = script_dir / "fxtd_ingest.py"
        assert fxtd_script.exists(), f"Sorry, we expected to find 'fxtd.sh' at {script_dir}!"
        return [
            "python3",
            str(fxtd_script),
            str(absolute),
        ]
