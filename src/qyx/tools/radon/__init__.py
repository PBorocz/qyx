"""Radon Module Configuration."""

import types
from typing import Callable

from qyx.tools._models_ import ToolDimension, ToolType
from qyx.tools.radon.models import RadonCc, RadonHal, RadonHalFunction, RadonMi, RadonRaw


# fmt: off
# Order here matters, when we ingest, we need to calculate summaries based on the
# lines of code metric from "Raw", thus, do this one FIRST!
DIMENSIONS = [
    ToolDimension("raw", "Raw Lines of Code"    , (RadonRaw,)                 , "raw" ),
    ToolDimension("hal", "Halstead Metrics"     , (RadonHal, RadonHalFunction), "hal" ),
    ToolDimension("cc" , "Cyclomatic Complexity", (RadonCc,)                  , "cc"  ),
    ToolDimension("mi" , "Maintainability Index", (RadonMi,)                  , "mi"  ),
]
# fmt: on


class Configuration(ToolType):
    """Configure semantics associated with using the various Radon tools."""

    def __init__(self, module: str):
        """Class meta-definition for the Radon tool."""
        super(Configuration, self).__init__(
            module=module,
            name="radon",
            description="Compute various code metrics",
            dimensions=DIMENSIONS,
            ingest_by_dimension=True,
        )

    def get_parse_save_method(self, dimension: ToolDimension) -> Callable:
        """Return the method to parse & save the specific Radon dimension's JSON output."""
        py_parse: types.ModuleType = self.import_component("parse")  # eg. .../tools/radon/parse.py
        return getattr(py_parse, f"parse_{dimension.cli_option.lower()}")  # eg. ingest_cc()
