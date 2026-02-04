"""."""

from argparse import Namespace

from rich import print as rprint

from mq.tools import generate_ta_pairs


def report(args: Namespace) -> None:
    for o_tool, analysis in generate_ta_pairs(args):
        if o_tool.render_cli_method:
            o_tool.render_cli_method(args, o_tool, analysis)
        else:
            rprint("[red]Sorry, unable to run reports for this tool as it doesn't have command-line rendering.[/red]")
