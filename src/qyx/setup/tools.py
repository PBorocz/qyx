"""Setup our tools configuration."""

import logging
import shutil
from argparse import Namespace
from importlib import import_module
from pathlib import Path
from types import ModuleType

from qyx.constants import ConfigurationError
from qyx.tools._models_ import Tools, ToolType

log = logging.getLogger(__name__)


################################################################################################
# "Setup" logic for dynamically identifying available modules and their respective configurations
################################################################################################
def setup_tools(args: Namespace) -> Tools:
    """Introspect our tools directory to dynamically discover tool modules defined right now!."""
    o_tools: dict = Tools()

    # Iterate over /app/tools and get handles to each module
    tools_dir: Path = Path("src/qyx/tools")
    for tool_path in tools_dir.iterdir():
        if tool_path.is_dir() and not tool_path.name.startswith("_"):
            log.debug(f"Setting up tool {tool_path.name:6s} from {tool_path=}...")

            ################################################################################
            # Get a handle to the module itself.
            ################################################################################
            try:
                s_import_path: str = f"qyx.tools.{tool_path.name}"
                tool_module: ModuleType = import_module(s_import_path)
            except ImportError as exc:
                raise ConfigurationError(f"Sorry, can't import: '{s_import_path}': {exc}!")

            ################################################################################
            # Now, find the configuration class
            ################################################################################
            try:
                tool_configuration_class: ToolType = getattr(tool_module, "Configuration")
            except AttributeError as exc:
                raise ConfigurationError(f"Sorry, can't instantiate {tool_module}'s configuration class?: {exc}!")

            ################################################################################
            # Instantiate it but validate before making available!
            ################################################################################
            o_tool = tool_configuration_class(module=tool_path.name)
            if issues := validate_tool(args, o_tool):
                log.warning(f"Sorry, encountered the following issues, '{o_tool.name}' is NOT available for use!")
                for issue in issues:
                    log.warning(issue)
                continue

            ################################################################################
            # Good to use!
            ################################################################################
            o_tools[o_tool.name] = o_tool

    log.debug(f"{len(o_tools)} tools available: {o_tools.display_names()}")
    args.tools = o_tools


def validate_tool(args: Namespace, o_tool: ToolType) -> list[str] | None:
    """Validate the tool before we allow it to be used/referred to."""
    issues = []

    ################################################################################################
    # 1: Validate that the tool is actually available on our path..
    #    (we assume that the first entry of the ingest command is the actual tool executable)
    # FIXME: The first entry is usually something like "uvx", ALSO important to check the second arg! (duh)
    ################################################################################################
    ingest_command = o_tool.get_ingest_command(args, relative="", absolute="")
    if not ingest_command:
        issues.append("- Couldn't get ingest_command?")
    executable = ingest_command[0]
    if not shutil.which(executable):
        issues.append(f"- Couldn't find {executable=} on your path!")

    return issues
