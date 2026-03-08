"""Radon Module Configuration."""

from enum import Enum

from qyx.constants import ReportLevel as Rl
from qyx.tools.base import ToolType
from qyx.tools.scc.models import Scc, SccFile


class AnalysisType(str, Enum):
    """Scc analysis types."""

    SCC = "scc"


class Configuration(ToolType):
    """Configure semantics associated with using the various Scc tools."""

    def __init__(self):
        """Class meta-definition for the Scc tool."""
        # fmt: off
        cli = {
            AnalysisType.SCC.value: (Rl.SUMMARY, Rl.DIRECTORY, Rl.FILE, Rl.HISTORY),
        }
        web = {
            AnalysisType.SCC.value: (Rl.SUMMARY, Rl.DIRECTORY, Rl.FILE, Rl.HISTORY),
        }

        super(Configuration, self).__init__(
            module="scc",
            name="scc",
            analyses={AnalysisType.SCC.value  : "SCC Code Counter"},
            models={AnalysisType.SCC.value: (Scc, SccFile)},
            reports=dict(cli=cli, web=web),
        )
        # fmt: off
