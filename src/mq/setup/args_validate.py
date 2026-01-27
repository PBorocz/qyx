"""."""

from argparse import Namespace

from rich import print as rprint

from mq.tools import split_arg_tool_analysis


def validate_args(args: Namespace) -> bool:
    """Validate arguments now that we've got everything setup."""
    # if args.command and args.command.lower() not in ("serve", "status"):
    #     if not getattr(args, "name", None) and not getattr(args, "path", None):
    #         rprint("[red]Sorry! one of either [bold]-n/--name[/bold] or  [bold]-p/--path[/bold] is required")
    #         return False
    # Commands that deal with projects may need BOTH a name and a path, others only a name.
    if args.command.lower() == "ingest":
        if not args.name:
            rprint("[red]Sorry! [bold]-n/--name[/bold] is required to perform an ingest!")
        if not args.path and not args.stdin:
            rprint(
                "[red]Sorry! you need to either specify [bold]-p/--path[/bold] "
                "OR provide data from [bold]--stdin[/bold] to perform an ingest.",
            )
            return False

    if args.command.lower() == "report":
        if not args.name:
            rprint("[red]Sorry! [bold]-n/--name[/bold] is required to report results.")
            return False
        # --name is OPTIONAL for status command.

    if "analysis" in args:
        tool, analysis, sub = split_arg_tool_analysis(args.tool_analysis)
        if tool not in args.tools:
            s_names = ", ".join(args.tools.keys())
            rprint(
                f"[red]Sorry! analysis: [bold]{args.tool_analysis}[/bold] is not valid, "
                f"tool must be one of:[/red] [blue]{s_names}[/blue]",
            )
            return False
    return True
