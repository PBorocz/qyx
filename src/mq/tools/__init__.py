"""..."""

import logging
from importlib import import_module
from argparse import Namespace
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
            # Now, find the configuration Class
            ################################################################################
            try:
                tool_configuration_class = getattr(tool_module, "Configuration")
                log.debug(f"{tool_configuration_class=}")
            except AttributeError as exc:
                raise RuntimeError(f"Sorry, can't instantiate {tool_name}'s configuration class?: {exc}!")

            ################################################################################
            # ...instantiate it and store it!
            ################################################################################
            tool_configuration_instance = tool_configuration_class()
            tool_configuration_instance.py_module = tool_module
            tools[tool_name] = tool_configuration_instance

    log.debug(f"Tools available: {', '.join(tools.keys())}")
    return tools


################################################################################################
# Misc. utilities functions
################################################################################################
def format_int_or_percentage(value: float, as_percentage: bool = False) -> str:
    return f"{value:.0f}%" if as_percentage else f"{value:,}"


################################################################################################
def generate_ta_pairs(args: Namespace) -> list[tuple[str, str]]:
    """Process the command-line argument and return a list of Tools and analyses to perform."""
    ################################################################################
    # Case 1: tool_analysis is empty -> we want to ingest everything!
    ################################################################################
    return_: list = list()
    if not args.tool_analysis:
        for tool_name in args.tools.keys():
            tool_configuration = args.tools[tool_name]
            for analysis_name in tool_configuration.analyses:
                return_.append((tool_configuration, analysis_name))
        return return_

    s_tool, s_analysis = split_arg_tool_analysis(args.tool_analysis)

    ################################################################################
    # Case 2: Tool only, give all the analyses the tool supports
    ################################################################################
    if not s_analysis:
        tool_configuration = args.tools[s_tool]
        for analysis_name in tool_configuration.analyses:
            return_.append((tool_configuration, analysis_name))
        return return_

    ################################################################################
    # Case 3: Tool *AND* Analysis specified!
    ################################################################################
    assert s_tool and s_analysis
    return [(args.tools[s_tool], s_analysis)]


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
