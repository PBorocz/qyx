"""..."""

import logging
from abc import ABC
from importlib import import_module
from argparse import Namespace
from pathlib import Path

from mq.tools.base import Scan

log = logging.getLogger(__name__)


################################################################################################
class AbstractModuleConfiguration(ABC):
    """Defines all the semantics of a code quality tool (aka module) supported by this package."""

    def __init__(
        self,
        module: str,  # Name of the python module directory supporting the tool
        analyses: tuple[str],
        **kwargs,
    ) -> "AbstractModuleConfiguration":
        """..."""
        self.module = module
        self.analyses: tuple[str] = analyses  # Analyses support by the tool (even if 1 for stuff like cloc and ruff)
        self.results_required = True  # Are Results "required" for a Scan to be valid? (usually yes)

        for attr, value in kwargs.items():
            setattr(self, attr, value)

    def get_ingest_command(self, *args, **kwargs):
        """..."""
        raise NotImplementedError("Sorry, this method needs to be implemented by an inherited class!")

    def get_parse_methods(self, *args, **kwargs):
        """..."""
        raise NotImplementedError("Sorry, this method needs to be implemented by an inherited class!")


################################################################################################
def save_scan_results(scan: Scan, rows: list) -> int:
    for row in rows:
        row.scan = scan.id
        row.save()
    return len(rows)


################################################################################################
def split_arg_tool_analysis(arg: str = None) -> tuple[str, str]:
    """Split the input argument that embeds tool & analysis together.

    ""          -> [None, None]
    "cloc"      -> ["cloc", None]
    "radon:raw" -> ["radon", "raw"]
    """
    if not arg:
        return [None, None]
    if ":" in arg:
        tool, analysis = arg.lower().split(":")
        return [tool, analysis]  # Tool + specific analysis
    return [arg.lower(), False]  # Tool only


################################################################################################
# "Setup" logic for dynamically identifying available modules and their respective configurations
################################################################################################
def setup_tools(args: Namespace) -> dict:
    """Introspect our tools directory to dynamically discover modules defined at run-time."""
    tools = {}

    # Iterate over /app/tools and get handles to each module
    tools_dir = Path("src/mq/tools")
    for tool_path in tools_dir.iterdir():
        if tool_path.is_dir() and not tool_path.name.startswith("_"):
            tool_name = tool_path.name
            log.debug(f"Setting up module: '{tool_name}'...")

            ################################################################################
            # Get a handle to the module itself.
            ################################################################################
            try:
                s_import_path = f"mq.tools.{tool_name}"
                tool = import_module(s_import_path)
            except ImportError as exc:
                raise RuntimeError(f"Sorry, can't import: '{s_import_path}': {exc}!")

            ################################################################################
            # Now, find the configuration Class
            ################################################################################
            try:
                tool_class = getattr(tool, "Configuration")
                log.debug(f"{tool_class=}")
            except AttributeError as exc:
                raise RuntimeError(f"Sorry, can't instantiate {tool_name}'s configuration class?: {exc}!")

            ################################################################################
            # ...instantiate it and store it!
            ################################################################################
            tools[tool_name] = tool_class()

    log.debug(f"Tools available: {', '.join(tools.keys())}")
    return tools


################################################################################################
# Misc. utilities functions
################################################################################################
def format_int_or_percentage(value, as_percentage):
    return f"{value:.0f}%" if as_percentage else f"{value:,}"
