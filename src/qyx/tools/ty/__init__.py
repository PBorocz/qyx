"""Ty Module Configuration."""

from enum import Enum

from qyx.constants import ReportLevel as Rl
from qyx.tools.base import ToolType
from qyx.tools.ty.models import Ty


class AnalysisType(str, Enum):
    """Ty analysis types."""

    TY = "ty"


class Configuration(ToolType):
    """Configure semantics associated with using the ruff tool."""

    def __init__(self):
        """..."""
        cli = {
            AnalysisType.TY.value: (Rl.SUMMARY, Rl.DIRECTORY, Rl.FILE, Rl.GRANULAR, Rl.DERIVED, Rl.HISTORY),
        }
        web = {
            AnalysisType.TY.value: (Rl.SUMMARY, Rl.DIRECTORY, Rl.FILE, Rl.GRANULAR, Rl.DERIVED, Rl.HISTORY),
        }

        super(Configuration, self).__init__(
            module="ty",
            name="ty",
            analyses={AnalysisType.TY.value: "TypeChecker"},
            models=dict(ty=(Ty,)),
            reports=dict(cli=cli, web=web),
            results_required=False,  # In this case,  Ty Scans without data ARE valid (albeit rare?)
        )
