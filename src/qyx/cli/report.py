"""."""

from argparse import Namespace

from rich import print as rprint

from qyx.tools import generate_ta_pairs
from qyx.tools._models_ import Project


def report(args: Namespace) -> None:
    for project in Project.iter_from_args(args):
        for o_tool, analysis in generate_ta_pairs(args):
            if o_tool.render_cli_method:
                o_tool.render_cli_method(args, project, o_tool, analysis)
            else:
                rprint(
                    "[red]Sorry, unable to run reports for this tool as it doesn't have command-line rendering.[/red]",
                )
