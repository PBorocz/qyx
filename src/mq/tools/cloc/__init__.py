"""Cloc Module Configuration."""

from enum import Enum

from mq.constants import ReportLevel as Rl
from mq.tools.base import ToolType
from mq.tools.cloc.models import Cloc


class ClocAnalysisType(str, Enum):
    """Cloc analysis types."""

    CLOC = "cloc"

    @property
    def description(self) -> str:
        """More granular definitions."""
        descriptions = {
            "cloc": "Count lines of code ('cloc')",
        }
        return descriptions.get(self.value, "-")


class Configuration(ToolType):
    """Configure semantics associated with using the cloc tool."""

    def __init__(self):
        """..."""
        cli = {
            "cloc": (Rl.SUMMARY, Rl.DIRECTORY, Rl.FILE, Rl.DERIVED, Rl.HISTORY),
        }
        web = {
            "cloc": (Rl.SUMMARY, Rl.DIRECTORY, Rl.FILE, Rl.DERIVED, Rl.HISTORY),
        }

        super(Configuration, self).__init__(
            module="cloc",
            name="cloc",
            analyses=[enum.value for enum in ClocAnalysisType],
            models=dict(cloc=(Cloc,)),
            reports=dict(cli=cli, web=web),
        )

    def get_ingest_command(self, relative: str = None, absolute: str = None, analysis: str = None) -> list[str]:
        """Return the command sent to subprocess to directly perform a CLOC operation."""
        return [
            "cloc",
            "--by-file",
            "--include-lang=Python",
            "--json",
            "--vcs=git",
            absolute,
        ]
