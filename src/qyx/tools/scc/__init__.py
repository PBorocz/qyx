"""Scc Module Configuration."""

from enum import Enum

from qyx.constants import ReportLevel as Rl
from qyx.tools._models_ import ToolType
from qyx.tools.scc.models import Scc, SccFile


class AnalysisType(str, Enum):
    """Scc analysis types."""

    SCC = "scc"


class Configuration(ToolType):
    """Configure semantics associated with using the Scc tool."""

    def __init__(self):
        """Class meta-definition for the Scc tool."""
        # fmt: off
        cli = {
            AnalysisType.SCC.value: (Rl.SUMMARY,),
        }
        web = {
            AnalysisType.SCC.value: (Rl.SUMMARY,),
        }

        super(Configuration, self).__init__(
            module="scc",
            name="scc",
            analyses={AnalysisType.SCC.value  : "Succint Code Counter"},
            models={AnalysisType.SCC.value: (Scc, SccFile)},
            reports=dict(cli=cli, web=web),
        )
        # fmt: off
