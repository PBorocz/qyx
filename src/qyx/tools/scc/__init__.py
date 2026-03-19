"""Scc Module Configuration."""

from qyx.tools._models_ import ToolDimension, ToolType
from qyx.tools.scc.models import Scc, SccFile


# fmt: off
DIMENSIONS = [
    ToolDimension("python"  , "Python"  , (Scc, SccFile)),
    ToolDimension("html"    , "HTML"    , (Scc, SccFile)),
    ToolDimension("css"     , "CSS"     , (Scc, SccFile)),
    ToolDimension("markdown", "Markdown", (Scc, SccFile)),
]
# fmt: on


class Configuration(ToolType):
    """Configure semantics associated with using the Scc tool."""

    def __init__(self, module: str):
        """Class meta-definition for the Scc tool."""
        # fmt: off
        super(Configuration, self).__init__(
            module=module,
            name="scc",
            description="Succinct code counter",
            dimensions=DIMENSIONS,
        )
        # fmt: off
