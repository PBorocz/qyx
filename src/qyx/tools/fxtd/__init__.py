"""FixMe ToDo Module Configuration."""

from argparse import Namespace
from enum import Enum
from pathlib import Path

from qyx.constants import ReportLevel as Rl
from qyx.tools.base import ToolType
from qyx.tools.fxtd.models import Fxtd


class AnalysisType(str, Enum):
    """Fxtd analysis types."""

    FXTD = "fxtd"


class Configuration(ToolType):
    """Configure semantics associated with using the tool."""

    def __init__(self):
        """..."""
        # fmt: off
        cli = dict(
            fxtd = (Rl.SUMMARY, Rl.DIRECTORY, Rl.FILE, Rl.HISTORY),
        )
        web = dict(
            fxtd = (Rl.SUMMARY, Rl.DIRECTORY, Rl.FILE, Rl.HISTORY),
        )
        # fmt: on
        super(Configuration, self).__init__(
            module="fxtd",
            name="fxtd",
            analyses={AnalysisType.FXTD.value: "FixMe's, ToDo's, Notes etc."},
            models=dict(fxtd=(Fxtd,)),
            results_required=False,  # In this case,  Scans without data ARE valid!
            reports=dict(cli=cli, web=web),
        )

    def get_ingest_command(
        self,
        args: Namespace,
        relative: str = None,
        absolute: str = None,
        analysis: str = None,
    ) -> list[str]:
        """Return the command sent to subprocess to directly perform the scan operation."""
        script_dir = Path(__file__).parent
        fxtd_tool = script_dir / "fxtd_tool.py"
        assert fxtd_tool.exists(), f"Sorry, we expected to find 'fxtd_tool.py' at {script_dir}!"
        return ["python3", str(fxtd_tool), str(absolute)]
