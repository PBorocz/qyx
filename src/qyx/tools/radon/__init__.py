"""Radon Module Configuration."""

import types
from enum import Enum
from typing import Callable

from qyx.constants import ReportLevel as Rl
from qyx.tools._models_ import ToolType
from qyx.tools.radon.models import RadonCc, RadonHal, RadonHalFunction, RadonMi, RadonRaw


class AnalysisType(str, Enum):
    """Radon analysis types."""

    # fmt: off
    CC  = "cc"
    HAL = "hal"
    MI  = "mi"
    RAW = "raw"
    # fmt: on


# Define the various report levels available for the CLI and Web-based report rendering.
# fmt: off
CLI_LEVELS_BY_ANALYSIS = {
    AnalysisType.CC.value  : (Rl.SUMMARY, Rl.DIRECTORY, Rl.FILE, Rl.GRANULAR, Rl.HISTORY),
    AnalysisType.HAL.value : (Rl.SUMMARY, Rl.DIRECTORY, Rl.FILE, Rl.GRANULAR, Rl.HISTORY),
    AnalysisType.MI.value  : (Rl.SUMMARY, Rl.DIRECTORY, Rl.FILE,              Rl.HISTORY),
    AnalysisType.RAW.value : (Rl.SUMMARY, Rl.DIRECTORY, Rl.FILE,              Rl.HISTORY),
}
WEB_LEVELS_BY_ANALYSIS = {
    AnalysisType.CC.value  : (Rl.SUMMARY, Rl.DIRECTORY, Rl.FILE, Rl.GRANULAR, Rl.HISTORY),
    AnalysisType.HAL.value : (Rl.SUMMARY, Rl.DIRECTORY, Rl.FILE, Rl.GRANULAR, Rl.HISTORY),
    AnalysisType.MI.value  : (Rl.SUMMARY, Rl.DIRECTORY, Rl.FILE,              Rl.HISTORY),
    AnalysisType.RAW.value : (Rl.SUMMARY, Rl.DIRECTORY, Rl.FILE,              Rl.HISTORY),
}
# fmt: on


class Configuration(ToolType):
    """Configure semantics associated with using the various Radon tools."""

    def __init__(self):
        """Class meta-definition for the Radon tool."""
        # fmt: off
        super(Configuration, self).__init__(
            module="radon",
            name="radon",
            analyses={
                AnalysisType.CC.value  : "Cyclomatic Complexity",
                AnalysisType.HAL.value : "Halstead Metrics",
                AnalysisType.MI.value  : "Maintainability Index",
                AnalysisType.RAW.value : "Raw Lines of Code",
            },
            models={
                AnalysisType.CC.value  : (RadonCc,),
                AnalysisType.HAL.value : (RadonHal, RadonHalFunction),
                AnalysisType.MI.value  : (RadonMi,),
                AnalysisType.RAW.value : (RadonRaw,),
            },
            reports=dict(cli=CLI_LEVELS_BY_ANALYSIS, web=WEB_LEVELS_BY_ANALYSIS),
        )
        # fmt: off

    def get_parse_method(self, analysis: str) -> Callable:
        """Return the method to parse & save this Radon analysis's JSON output."""
        py_parse: types.ModuleType = self.import_component("parse")  # eg. .../tools/radon/parse.py
        return getattr(py_parse, f"parse_{analysis.lower()}")  # eg. ingest_cc()
