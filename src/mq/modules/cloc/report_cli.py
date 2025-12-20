"""CLI report rendering obo 'cloc' tool."""

import logging
from argparse import Namespace

from mq.cli import cli_table, cli_console
from mq.modules import format_int_or_percentage as fmt
from mq.modules.base import Project, Run
from mq.modules.cloc import MODULE
from mq.modules.cloc.models import query
from mq.utils import format_timestamp_headers

log = logging.getLogger(__name__)


def report(args: Namespace) -> None:
    try:
        project = Project.get(Project.path_input == args.project)
    except Project.DoesNotExist:
        log.error(f"Sorry, we didn't find any data yet for project: {args.project}")
        return None

    # Get most recent Run for simple "current-state" reporting..
    if not (run := Run.get_most_recent(project, MODULE)):
        log.error("Sorry, we haven't performed a CLOC measurement yet for this project.")
        return None

    # Extract any/all module specific reporting options
    args.percentages = True if args.options and "percentage" in args.options.lower() else False

    match args.level.lower():
        case "s" | "summary":
            _summary(args, run)
        case "d" | "detail":
            _detail(args, run)
        case "f" | "full":
            _full(args, run)
        case "h" | "history":
            _history(args, project)
        case _:
            log.warning(f"Sorry, invalid report level: '{args.level}', run mq report --help for valid options.")


def _summary(args: Namespace, run: Run) -> None:
    result = query(args, "summary", run)
    table = cli_table(title=f"CLOC @ {run.timestamp_display}")
    table.add_column("Code", justify="center")
    table.add_column("Comment", justify="center")
    table.add_column("Blank", justify="center")
    table.add_column("TOTAL", justify="center")
    table.add_row(
        fmt(result.lines_code, args.percentages),
        fmt(result.lines_comment, args.percentages),
        fmt(result.lines_blank, args.percentages),
        fmt(result.lines_total, args.percentages),
    )
    cli_console.print(table)


def _detail(args: Namespace, run: Run, percentage: bool = False) -> None:
    grand_total = query(args, "summary", run)
    detail_rows = query(args, "detail", run)
    table = cli_table(title=f"CLOC @ {run.timestamp_display}", show_footer=True)
    table.add_column("Directory", justify="left", footer="TOTAL")
    table.add_column("Code", justify="right", footer=fmt(grand_total.lines_code, args.percentages))
    table.add_column("Comment", justify="right", footer=fmt(grand_total.lines_comment, args.percentages))
    table.add_column("Blank", justify="right", footer=fmt(grand_total.lines_blank, args.percentages))
    table.add_column("TOTAL", justify="right", footer=fmt(grand_total.lines_total, args.percentages))

    for result in detail_rows:
        table.add_row(
            result.dir,
            fmt(result.lines_code, args.percentages),
            fmt(result.lines_comment, args.percentages),
            fmt(result.lines_blank, args.percentages),
            fmt(result.lines_total, args.percentages),
        )
    cli_console.print(table)


def _full(args: Namespace, run: Run) -> None:
    rows, column_totals, grand_total = query(args, "full", run)

    table = cli_table(title=f"CLOC @ {run.timestamp_display}", show_footer=True)
    table.add_column("File", footer="TOTAL")
    table.add_column("Code", justify="right", footer=fmt(column_totals["lines_code"], args.percentages))
    table.add_column("Comment", justify="right", footer=fmt(column_totals["lines_comment"], args.percentages))
    table.add_column("Blank", justify="right", footer=fmt(column_totals["lines_blank"], args.percentages))
    table.add_column("TOTAL", justify="right", footer=fmt(grand_total, args.percentages))
    for row in rows:
        table.add_row(
            f"{row.dir}/{row.filename}",
            fmt(row.lines_code, args.percentages),
            fmt(row.lines_comment, args.percentages),
            fmt(row.lines_blank, args.percentages),
            fmt(row.lines_total, args.percentages),
        )
    cli_console.print(table)


def _history(args: Namespace, project: Project) -> None:
    timestamps, transposed, grand_totals = query(args, "history", project=project)
    timestamps_formatted = format_timestamp_headers(timestamps)
    table = cli_table(title="CLOC Results Over Time", show_footer=True)
    table.add_column("Metric", justify="left", footer="-")
    for timestamp in sorted(timestamps):
        table.add_column(
            timestamps_formatted[timestamp],
            justify="right",
            footer=str(grand_totals[timestamp]),
            footer_style="bold cyan",
        )

    for metric, dt_rows in transposed.items():
        row = [metric]
        for timestamp in sorted(timestamps):
            row.append(str(dt_rows[timestamp]))
        table.add_row(*row)

    cli_console.print(table)
