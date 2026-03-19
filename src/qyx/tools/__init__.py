"""..."""

import logging
from argparse import Namespace

from qyx.constants import ALL_ITEMS
from qyx.tools._models_ import ToolType

log = logging.getLogger(__name__)


################################################################################################
# Misc. utilities functions
################################################################################################
def format_int_or_percentage(value: float, as_percentage: bool = False) -> str:
    return f"{value:.0f}%" if as_percentage else f"{value:,}"


################################################################################################
def generate_ta_pairs(args: Namespace) -> list[ToolType]:
    """Process the command-line or interactive arguments and return a list of tool(s) to perform an ingest upon."""
    ################################################################################
    # Case 1: No tool specified -> we want to "process" everything!
    ################################################################################
    if not args.tool or args.tool == ALL_ITEMS:
        return args.tools.values()

    ################################################################################
    # Case 2: Lookup the specific tool by name.
    ################################################################################
    try:
        return [args.tools[args.tool.lower()]]
    except KeyError:
        raise RuntimeError(f"Sorry, unable to find {args.tool.lower()}!")
