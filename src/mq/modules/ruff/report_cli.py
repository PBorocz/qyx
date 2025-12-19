"""..."""

import logging
from argparse import Namespace

from mq.cli import cli_console, cli_table
from mq.modules.models import Project, Run
from mq.modules.ruff import MODULE
from mq.modules.ruff.models import query_detail, query_full, query_history, query_summary
from mq.utils import format_timestamp_headers, remove_common_prefixes

log = logging.getLogger(__name__)


def report(args: Namespace) -> None:
    try:
        project = Project.get(path_input=args.project)
    except Project.DoesNotExist:
        log.error(f"Sorry, we didn't find any data yet for project: {args.project}")
        return None

    # Get most recent Run for simple "current-state" reporting..
    if not (run := Run.get_most_recent(project, MODULE)):
        log.error(f"Sorry, we haven't performed a {MODULE.upper()} measurement yet for this project.")
        return None

    if args.last:
        _report_history(args, project)
    else:
        match args.level.lower():
            case "summary":
                _report_summary(args, run)
            case "detail":
                _report_detail(args, run)
            case "full":
                _report_full(args, run)
            case _:
                log.warning(f"Sorry, invalid report level {args.level}, must be one of 'summary' or 'detail'.")


def _report_summary(args: Namespace, run: Run) -> None:
    row = query_summary(args, run)
    table = cli_table(title=f"RUFF: {run.timestamp_display}", show_header=False)
    table.add_column("_", style="bold magenta")
    table.add_column("_", style="bold magenta")
    table.add_row("Ruff Issues", str(row.count()))
    cli_console.print(table)


def _report_detail(args: Namespace, run: Run) -> None:
    results = query_detail(args, run)
    table = cli_table(title=f"RUFF: {run.timestamp_display}")
    table.add_column("Rule")
    table.add_column("Count", justify="center")
    table.add_column("Message")
    for result in results:
        table.add_row(result.rule_code, str(result.count), result.message)
    cli_console.print(table)


def _report_full(args: Namespace, run: Run) -> None:
    rows = query_full(args, run)
    foobar = 1
    rows = remove_common_prefixes(rows)
    table = cli_table(title=f"RUFF: {run.timestamp_display}")
    table.add_column("Rule")
    table.add_column("File (line)")
    table.add_column("Message")
    for row in rows:
        table.add_row(row.rule_code, f"{row.filename} [{row.line}] ", row.message)
    cli_console.print(table)


def _report_history(args: Namespace, project: Project) -> None:
    """Report on the args.last number of runs "across"."""
    rows, messages, transposed, grand_totals = query_history(args, project)
    ################################################################################################
    # Render the table
    ################################################################################################
    table = cli_table(title="RUFF Results Over Time")
    table.add_column("Rule", justify="left", footer="-")
    table.add_column("Message", justify="left", footer="-")
    timestamps = list({row.timestamp for row in rows})
    timestamps_formatted = format_timestamp_headers(timestamps)
    for timestamp in sorted(timestamps):
        table.add_column(
            timestamps_formatted[timestamp],
            justify="right",
            footer=str(grand_totals[timestamp]),
            footer_style="bold cyan",
        )

    for rule_code, dt_rows in transposed.items():
        row = [rule_code, messages[rule_code]]
        for timestamp in sorted(timestamps):
            row.append(str(dt_rows[timestamp]))
        table.add_row(*row)

    cli_console.print(table)
