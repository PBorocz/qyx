"""Setup our tools configuration."""

import logging
import shutil
import subprocess
from argparse import Namespace
from importlib import import_module
from importlib.resources import files
from importlib.resources.abc import Traversable
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

    # Iterate over qyx/tools and get handles to each module
    tools_dir: Traversable = files("qyx").joinpath("tools")
    for tool_path in tools_dir.iterdir():
        if tool_path.is_dir() and not tool_path.name.startswith("_"):
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
            if issue := validate_tool(args, o_tool):
                log.warning(issue)
                log.warning(f"Sorry, '{o_tool.name}' is NOT available for use!")

            ################################################################################
            # Good to use!
            ################################################################################
            o_tools[o_tool.name] = o_tool
            log.debug(f"Successfully setup tool {tool_path.name}")

    args.tools = o_tools


def validate_tool(args: Namespace, o_tool: ToolType) -> str | None:
    """Validate the tool before we allow it to be used/referred to."""
    ################################################################################################
    # 1: Make sure we can find an "ingest" command from our configuration file.
    # 2: Validate that the tool used in the command is actually available on our path...
    #    (we assume that the first entry of the ingest command is the actual tool executable)
    ################################################################################################
    ingest_command = o_tool.get_ingest_command(args, relative="", absolute="")
    if not ingest_command:
        return "❌ Couldn't get ingest_command?"

    executable = ingest_command[0]
    if executable in ("uvx",):  # Special case
        if not shutil.which("uvx"):
            return "❌ Couldn't find 'uvx' on your path, is it installed?"

        # Take the target of uvx and check that also!
        executable = ingest_command[1]
        if not __check_uvx_tool(executable):
            return f"❌ Couldn't run 'uvx {executable}', is it installed into uvx?"

    else:
        # Normal case:
        if not shutil.which(executable):
            return f"❌ Couldn't find {executable=} on your path, is it installed?"

    return None


def __check_uvx_tool(tool_name) -> bool:
    try:
        result = subprocess.run(["uvx", tool_name, "--version"], capture_output=True, timeout=30)
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False
