"""..."""

import logging
from argparse import Namespace

from mq.tools.base import ToolType

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
    # Case 1: No analysis specified -> we want to "process" everything!
    ################################################################################
    if not args.analysis or args.analysis == "*":  # SENTINEL!
        return_: list = list()
        for tool_name in args.tools.keys():
            o_tool: ToolType = args.tools[tool_name]
            for analysis_name in o_tool.analyses:
                return_.append((o_tool, analysis_name))
        return return_

    # Is the arg a "tool" or an analysis?
    if args.analysis.lower() in args.tools.keys():
        ################################################################################
        # Case 2: Tool only, return *all* the analyses the tool supports
        ################################################################################
        o_tool = args.tools[args.analysis.lower()]
        return [(o_tool, analysis) for analysis in o_tool.analyses]

    else:
        ################################################################################
        # Case 3: The arg is an analysis, find the matching tool for it.
        ################################################################################
        for tool_name in args.tools.keys():
            o_tool: ToolType = args.tools[tool_name]
            for analysis_name in o_tool.analyses:
                if args.analysis.lower() == analysis_name.lower():
                    # Found it!
                    return [(o_tool, analysis_name)]

    raise RuntimeError("Sorry, we already validated args.analysis but couldn't find a tool or analysis?")
