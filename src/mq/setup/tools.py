"""Setup our tools configuration."""

import logging
from argparse import Namespace
from importlib import import_module
from pathlib import Path

log = logging.getLogger(__name__)


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
                tool_module = import_module(s_import_path)
            except ImportError as exc:
                raise RuntimeError(f"Sorry, can't import: '{s_import_path}': {exc}!")

            ################################################################################
            # Now, find the configuration class
            ################################################################################
            try:
                tool_configuration_class = getattr(tool_module, "Configuration")
                log.debug(f"{tool_configuration_class=}")
            except AttributeError as exc:
                raise RuntimeError(f"Sorry, can't instantiate {tool_name}'s configuration class?: {exc}!")

            ################################################################################
            # ...instantiate it and store it!
            ################################################################################
            tools[tool_name] = tool_configuration_class()

    log.debug(f"Tools available: {', '.join(tools.keys())}")
    args.tools = tools
    # return tools
