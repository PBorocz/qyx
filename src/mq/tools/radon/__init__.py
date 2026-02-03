"""Radon Module Configuration."""

import types
from enum import Enum
from typing import Callable

from mq.constants import ReportLevel as Rl
from mq.tools.base import ToolType
from mq.tools.radon.models import RadonCc, RadonHal, RadonHalFunction, RadonMi, RadonRaw

COLORS: dict = dict(positive="red", negative="green", neutral="white")


class RadonAnalysisType(str, Enum):
    """Radon analysis types."""

    # fmt: off
    CC  = "cc"
    HAL = "hal"
    MI  = "mi"
    RAW = "raw"
    # fmt: on

    @property
    def description(self) -> str:
        """More granular definitions."""
        descriptions = {
            "cc": "Cyclomatic Complexity",
            "hal": "Halstead Metrics",
            "mi": "Maintainability Index",
            "raw": "Raw Lines of Code",
        }
        return descriptions.get(self.value, "-")


class RadonCcEntityType(str, Enum):
    """Radon's Cyclomatic Complexity Entity Types."""

    # fmt: off
    CLASS    = "C"
    FUNCTION = "F"
    METHOD   = "M"
    # fmt: on

    @property
    def plural(self) -> str:
        """Return the plural."""
        plurals = dict(C="Classes", F="Functions", M="Methods")
        return plurals.get(self.value.upper(), "-")


# Define the various report levels available for the CLI and Web-based report rendering.
# fmt: off
CLI_LEVELS_BY_ANALYSIS = {
    RadonAnalysisType.CC.value  : (Rl.SUMMARY, Rl.DIRECTORY, Rl.FILE, Rl.DETAIL, Rl.DERIVED, Rl.HISTORY),
    RadonAnalysisType.HAL.value : (Rl.SUMMARY, Rl.DIRECTORY, Rl.FILE, Rl.DETAIL, Rl.DERIVED, Rl.HISTORY),
    RadonAnalysisType.MI.value  : (Rl.SUMMARY, Rl.DIRECTORY, Rl.FILE,            Rl.DERIVED, Rl.HISTORY),
    RadonAnalysisType.RAW.value : (Rl.SUMMARY, Rl.DIRECTORY, Rl.FILE,                        Rl.HISTORY),
}
WEB_LEVELS_BY_ANALYSIS = {
    RadonAnalysisType.CC.value  : (Rl.SUMMARY, Rl.DIRECTORY, Rl.FILE, Rl.DETAIL, Rl.DERIVED, Rl.HISTORY),
    RadonAnalysisType.HAL.value : (Rl.SUMMARY, Rl.DIRECTORY, Rl.FILE, Rl.DETAIL, Rl.DERIVED, Rl.HISTORY),
    RadonAnalysisType.MI.value  : (Rl.SUMMARY, Rl.DIRECTORY, Rl.FILE,            Rl.DERIVED, Rl.HISTORY),
    RadonAnalysisType.RAW.value : (Rl.SUMMARY, Rl.DIRECTORY, Rl.FILE,                        Rl.HISTORY),
}
# fmt: on


class Configuration(ToolType):
    """Configure semantics associated with using the various Radon tools."""

    def __init__(self):
        """Class meta-definition for the Radon tool."""
        super(Configuration, self).__init__(
            module="radon",
            name="radon",
            analyses=[enum.value for enum in RadonAnalysisType],
            models={
                RadonAnalysisType.CC.value: (RadonCc,),
                RadonAnalysisType.HAL.value: (RadonHal, RadonHalFunction),
                RadonAnalysisType.MI.value: (RadonMi,),
                RadonAnalysisType.RAW.value: (RadonRaw,),
            },
            reports=dict(cli=CLI_LEVELS_BY_ANALYSIS, web=WEB_LEVELS_BY_ANALYSIS),
        )

    def get_ingest_command(self, relative: str = None, absolute: str = None, analysis: str = None) -> list[str]:
        """Return the command sent to subprocess to directly perform an ingest operation."""
        if not analysis:
            raise RuntimeError("Sorry, we need a sub_module here!")
        return [
            "uvx",
            "radon",
            analysis,
            "--json",
            absolute,
        ]

    def get_ingest_method(self, analysis: str) -> Callable:
        """Return the ingest method to parse & save this Radon analysis's JSON output."""
        py_ingest: types.ModuleType = self.import_component("ingest")  # eg. .../<module>/ingest.py
        return getattr(py_ingest, f"ingest_{analysis.lower()}")  # eg. ingest_cc()
