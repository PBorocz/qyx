"""Ty Module Configuration."""

from qyx.tools._models_ import ToolDimension, ToolType
from qyx.tools.ty.models import Ty

DIMENSIONS = [
    ToolDimension("ty", "Astral type checker", (Ty,)),
]


class Configuration(ToolType):
    """Configure semantics associated with using the ruff tool."""

    def __init__(self, module: str):
        """..."""
        super(Configuration, self).__init__(
            module=module,
            name="ty",
            description="Astral type checker",
            dimensions=DIMENSIONS,
        )
