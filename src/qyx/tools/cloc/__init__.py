"""Cloc Module Configuration."""

from enum import Enum

from qyx.constants import ReportLevel as Rl
from qyx.tools.base import ToolType
from qyx.tools.cloc.models import Cloc


class AnalysisType(str, Enum):
    """Cloc analysis types."""

    CLOC = "cloc"


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
            analyses={AnalysisType.CLOC.value: "cloc - Count lines of code"},
            models=dict(cloc=(Cloc,)),
            reports=dict(cli=cli, web=web),
        )
