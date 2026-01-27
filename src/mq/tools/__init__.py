"""..."""

import logging
from argparse import Namespace

log = logging.getLogger(__name__)


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
            for analysis_name in tool_configuration.models.keys():
                if analysis_name.startswith("_"):
                    continue
                return_.append((tool_configuration, analysis_name))
        return return_

    s_tool, s_analysis = split_arg_tool_analysis(args.tool_analysis)

    ################################################################################
    # Case 2: Tool only, give all the analyses the tool supports
    ################################################################################
    if not s_analysis:
        tool_configuration = args.tools[s_tool]
        for analysis_name in tool_configuration.models.keys():
            if analysis_name.startswith("_"):
                continue
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
