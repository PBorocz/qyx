"""FixMe ToDo Module Configuration."""

from argparse import Namespace
from pathlib import Path

from qyx.tools._models_ import ToolDimension, ToolType
from qyx.tools.fxtd.models import Fxtd


DIMENSIONS = [
    ToolDimension("fxtd", "Fixme's, ToDo's, Notes etc.", (Fxtd,)),
]


class Configuration(ToolType):
    """Configure semantics associated with using the tool."""

    def __init__(self, module: str):
        """..."""
        super(Configuration, self).__init__(
            module=module,
            name="fxtd",
            description="FixMe's, ToDo's, Notes etc.",
            dimensions=DIMENSIONS,
            results_required=False,  # In this case,  Scans without data ARE valid!
        )

    def get_ingest_command(
        self,
        args: Namespace,
        relative: str = None,
        absolute: str = None,
        dimension: ToolDimension = None,
        **kwargs,
    ) -> list[str]:
        """Return the command sent to subprocess to directly perform the scan operation."""
        script_dir = Path(__file__).parent
        fxtd_tool = script_dir / "fxtd_tool.py"
        assert fxtd_tool.exists(), f"Sorry, we expected to find 'fxtd_tool.py' at {script_dir}!"
        return ["python3", str(fxtd_tool), str(absolute)]
