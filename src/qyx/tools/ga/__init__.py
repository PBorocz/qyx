"""Ga (or git activity) Module Configuration."""

from argparse import Namespace
from pathlib import Path

from qyx.tools._models_ import ToolDimension, ToolType
from qyx.tools.ga.models import Ga

# fmt: off
DIMENSIONS = [
    ToolDimension("authorship"        , "Authorship"         , (Ga,)),
    ToolDimension("bug_commits"       , "Bug Commits"        , (Ga,)),
    ToolDimension("commit_frequency"  , "Commit Frequency"   , (Ga,)),
    ToolDimension("emergency_commits" , "Emergency Commits"  , (Ga,)),
    ToolDimension("file_churn"        , "Files Most Touched" , (Ga,)),
]
# fmt: on


class Configuration(ToolType):
    """Configure semantics associated with using the ruff tool."""

    def __init__(self, module: str):
        """..."""
        super(Configuration, self).__init__(
            module=module,
            name="ga",
            description="Git Analytics",
            dimensions=DIMENSIONS,
            ingest_latest_only=True,
        )

    def get_ingest_command(self, args: Namespace, absolute: str, **kwargs) -> list[str]:
        """Return the command sent to subprocess to directly gather git information."""
        script_dir = Path(__file__).parent
        ga_script_path = script_dir / "ga_tool.py"
        assert ga_script_path.exists(), f"Sorry, we expected to find 'ga_tool.py' at {script_dir}!"
        return ["python3", str(ga_script_path), str(absolute)]
