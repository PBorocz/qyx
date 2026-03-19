"""Cloc Module Configuration."""

from qyx.tools._models_ import ToolDimension, ToolType
from qyx.tools.cloc.models import Cloc


DIMENSIONS = [
    ToolDimension("cloc", "Count lines of code", (Cloc,)),
]


class Configuration(ToolType):
    """Configure semantics associated with using the cloc tool."""

    def __init__(self, module: str):
        """..."""
        super(Configuration, self).__init__(
            module=module,
            name="cloc",
            description="Count lines of code",
            dimensions=DIMENSIONS,
        )
