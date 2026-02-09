"""Cloc Module Configuration."""

from enum import Enum

from mq.constants import ReportLevel as Rl
from mq.tools.base import ToolType
from mq.tools.cloc.models import Cloc


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
            analyses={AnalysisType.CLOC.value: "Count lines of code ('cloc')"},
            models=dict(cloc=(Cloc,)),
            reports=dict(cli=cli, web=web),
        )
