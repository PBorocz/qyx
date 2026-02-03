"""FixMe ToDo Module Configuration."""

from enum import Enum
from pathlib import Path

from mq.constants import ReportLevel as Rl
from mq.tools.base import ToolType
from mq.tools.fxtd.models import Fxtd

COLORS: dict = dict(positive="red", negative="green", neutral="white")


class FxtdAnalysisType(str, Enum):
    """Fxtd analysis types."""

    FXTD = "fxtd"

    @property
    def description(self) -> str:
        """More granular definitions."""
        descriptions = {
            "fxtd": "FixMe, ToDo's etc.",
        }
        return descriptions.get(self.value, "-")


class Configuration(ToolType):
    """Configure semantics associated with using the tool."""

    def __init__(self):
        """..."""
        # fmt: off
        cli = dict(
            fxtd = (Rl.SUMMARY, Rl.DIRECTORY, Rl.FILE, Rl.DERIVED, Rl.HISTORY),
        )
        web = dict(
            fxtd = (Rl.SUMMARY, Rl.DIRECTORY, Rl.FILE, Rl.DERIVED, Rl.HISTORY),
        )
        # fmt: on
        super(Configuration, self).__init__(
            module="fxtd",
            name="fxtd",
            analyses=[enum.value for enum in FxtdAnalysisType],
            models=dict(fxtd=(Fxtd,)),
            results_required=False,  # In this case,  Scans without data ARE valid!
            reports=dict(cli=cli, web=web),
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
