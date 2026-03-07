"""..."""

import logging
from argparse import Namespace

from qyx.constants import ALL_ITEMS
from qyx.tools.base import ToolType

log = logging.getLogger(__name__)


################################################################################################
# Misc. utilities functions
################################################################################################
def format_int_or_percentage(value: float, as_percentage: bool = False) -> str:
    return f"{value:.0f}%" if as_percentage else f"{value:,}"


################################################################################################
def generate_ta_pairs(args: Namespace) -> list[tuple[ToolType, str]]:
    """Process the command-line argument and return a list of Tools and analyses to perform."""
    ################################################################################
    # Case 1: No analysis specified -> we want to "process" everything!
    ################################################################################
    if not args.analysis or args.analysis == ALL_ITEMS:
        return args.tools.tools_analyses()

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
        for o_tool in args.tools.tools():
            for analysis_name in o_tool.analyses:
                if args.analysis.lower() == analysis_name.lower():
                    return [(o_tool, analysis_name)]  # Found it!

    raise RuntimeError("Sorry, we already validated args.analysis but couldn't find a tool or analysis?")
