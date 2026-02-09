"""Setup our tools configuration."""

import logging
import shutil
from argparse import Namespace
from importlib import import_module
from pathlib import Path
from types import ModuleType

from mq.constants import ConfigurationError
from mq.tools.base import ToolType

log = logging.getLogger(__name__)


################################################################################################
# "Setup" logic for dynamically identifying available modules and their respective configurations
################################################################################################
def setup_tools(args: Namespace) -> dict:
    """Introspect our tools directory to dynamically discover modules defined at run-time."""
    tools: dict = {}

    # Iterate over /app/tools and get handles to each module
    tools_dir: Path = Path("src/mq/tools")
    for tool_path in tools_dir.iterdir():
        if tool_path.is_dir() and not tool_path.name.startswith("_"):
            tool_name: str = tool_path.name
            log.debug(f"Setting up module: '{tool_name}'...")

            ################################################################################
            # Get a handle to the module itself.
            ################################################################################
            try:
                s_import_path: str = f"mq.tools.{tool_name}"
                tool_module: ModuleType = import_module(s_import_path)
            except ImportError as exc:
                raise ConfigurationError(f"Sorry, can't import: '{s_import_path}': {exc}!")

            ################################################################################
            # Now, find the configuration class
            ################################################################################
            try:
                tool_configuration_class: ToolType = getattr(tool_module, "Configuration")
            except AttributeError as exc:
                raise ConfigurationError(f"Sorry, can't instantiate {tool_name}'s configuration class?: {exc}!")

            ################################################################################
            # Instantiate it but validate before making available!
            ################################################################################
            o_tool = tool_configuration_class()
            if issues := validate_tool(args, o_tool):
                log.warning(f"Sorry, encountered the following issues, '{o_tool.name}' is NOT available for use!")
                for issue in issues:
                    log.warning(issue)
                continue

            ################################################################################
            # Good to use!
            ################################################################################
            tools[tool_name] = o_tool

    log.debug(f"{len(tools)} tools available: {', '.join(tools.keys())}")
    args.tools = tools


def validate_tool(args: Namespace, o_tool: ToolType) -> list[str] | None:
    """Validate the tool before we allow it to be used/referred to."""
    issues = []

    ################################################################################################
    # 1: Validate that the tool is actually available on our path..
    #    (we assume that the first entry of the ingest command is the actual tool executable)
    ################################################################################################
    ingest_command = o_tool.get_ingest_command(args, relative="", absolute="", analysis="anAnalysis")
    executable = ingest_command[0]
    if not shutil.which(executable):
        issues.append(f"- Couldn't find {executable=} on your path!")

    # ...

    return issues
