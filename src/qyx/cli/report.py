"""."""

from argparse import Namespace

from rich import print as rprint

from qyx.constants import ALL_ITEMS
from qyx.tools._models_ import Project
from qyx.tools._models_ import ToolDimension, ToolType


def report(args: Namespace) -> None:
    for project in Project.iter_from_args(args):
        for o_tool, dimension in _get_tools_dimensions_to_report(args):
            if o_tool.render_cli_method:
                o_tool.render_cli_method(args, project, o_tool, dimension)
            else:
                rprint(
                    "[red]Sorry, unable to run reports for this tool as it doesn't have command-line rendering.[/red]",
                )


def _get_tools_dimensions_to_report(args: Namespace) -> list[tuple[ToolType, ToolDimension]]:
    """Process the command-line argument and return a list of tools and dimensions to report on."""
    o_tool = args.tools[args.tool.lower()]

    ################################################################################
    # Case 1: Both tool and dimension are explicitly specified:
    ################################################################################
    if args.dimension and args.dimension != ALL_ITEMS:
        for o_dim in o_tool.dimensions:
            if args.dimension.lower() in (o_dim.name.lower(), o_dim.description.lower()):
                return [(o_tool, o_dim)]  # Found it!
        msg = f"Sorry, unable to find dimension='{args.dimension}' for tool='{args.tool}' even after validation!"
        raise RuntimeError(msg)

    ################################################################################
    # Case 2: Dimension is wildcarded
    ################################################################################
    if args.dimension == ALL_ITEMS:
        return [(o_tool, o_dim) for o_dim in o_tool.dimensions]

    ################################################################################
    # Case 3: Dimension specified but tool is not.
    ################################################################################
    # For now, don't handle this case...we don't want dimension names to have to
    # be unique across tools so we want to enforce having a tool specified.
    raise NotImplementedError(f"Sorry, we need a tool from which to lookup dimension='{args.dimension}'")
