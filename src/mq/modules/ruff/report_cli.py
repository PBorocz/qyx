"""..."""

import logging
from argparse import Namespace

from mq.cli import cli_console, cli_table
from mq.modules.base import Project, Run
from mq.modules.ruff import COLORS, MODULE
from mq.modules.ruff.models import query
from mq.utils import format_timestamp_headers

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

    match args.level.lower():
        case "0":
            _report_0(args, run)
        case "1":
            _report_1(args, run)
        case "2":
            _report_2(args, run)
        case "h":
            _report_h(args, project)
        case _:
            log.warning(f"Sorry, invalid report level: '{args.level}', run mq report --help for valid options.")


def _report_0(args: Namespace, run: Run) -> None:
    row = query(args, "0", run)
    table = cli_table(title=f"RUFF @ {run.timestamp_display}", show_header=False)
    table.add_column("_", style="bold magenta")
    table.add_column("_", style="bold magenta")
    table.add_row("Issues", f"{row.count():,d}")
    cli_console.print(table)


def _report_1(args: Namespace, run: Run) -> None:
    summary = query(args, "0", run)
    results = query(args, "1", run)
    table = cli_table(title=f"RUFF @ {run.timestamp_display}", show_footer=True)
    table.add_column("Rule", footer="TOTAL")
    table.add_column("Count", justify="center", footer=f"{summary.count():,}")
    table.add_column("Message")
    for result in results:
        table.add_row(result.rule_code, f"{result.count:,d}", result.message)
    cli_console.print(table)


def _report_2(args: Namespace, run: Run) -> None:
    rows = query(args, "2", run)
    table = cli_table(title=f"RUFF @ {run.timestamp_display}")
    table.add_column("Rule")
    table.add_column("File [line]")
    table.add_column("Message")
    for row in rows:
        table.add_row(row.rule_code, f"{row.dir}/{row.filename} [{row.line}] ", row.message)
    cli_console.print(table)


# History at the "0" level...
def _report_h(args: Namespace, project: Project) -> None:
    """Report on the history of runs "across"."""
    timestamps, rows, roc = query(args, "history", project=project)
    timestamps_formatted = format_timestamp_headers(timestamps)

    ################################################################################################
    # Render the table
    ################################################################################################
    table = cli_table(title="RUFF Results Over Time")
    table.add_column("-")
    for timestamp in sorted(timestamps):
        table.add_column(
            timestamps_formatted[timestamp],
            justify="right",
        )
    table.add_column("Delta")

    row = ["Issues"]
    for timestamp in sorted(timestamps):
        row.append(str(rows[timestamp]))

    if roc > 0.01:
        color = COLORS["positive"]
    elif roc < -0.01:
        color = COLORS["negative"]
    else:
        color = COLORS["neutral"]

    row.append(f"[{color}][bold]{roc:+.2f}%[/bold][/{color}]")

    table.add_row(*row)

    cli_console.print(table)


# History at the "1" level!
# def _report_history(args: Namespace, project: Project) -> None:
#     """Report on the history of runs "across"."""
#     rows, messages, transposed, grand_totals = query(args, "history", project=project)
#     ################################################################################################
#     # Render the table
#     ################################################################################################
#     table = cli_table(title="RUFF Results Over Time", show_footer=True)
#     table.add_column("Rule", justify="left", footer="TOTAL")
#     table.add_column("Message", justify="left", footer="")
#     timestamps = list({row.timestamp for row in rows})
#     timestamps_formatted = format_timestamp_headers(timestamps)
#     for timestamp in sorted(timestamps):
#         table.add_column(
#             timestamps_formatted[timestamp],
#             justify="right",
#             footer=str(grand_totals[timestamp]),
#             footer_style="bold cyan",
#         )

#     for rule_code, dt_rows in transposed.items():
#         row = [rule_code, messages[rule_code]]
#         for timestamp in sorted(timestamps):
#             row.append(str(dt_rows[timestamp]))
#         table.add_row(*row)

#     cli_console.print(table)
