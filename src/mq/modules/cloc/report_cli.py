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

    match args.level.lower():
        case "0":
            _summary(args, run)
        case "1":
            _detail(args, run)
        case "2":
            _full(args, run)
        case "h" | "history":
            _history(args, project)
        case _:
            log.warning(f"Sorry, invalid report level: '{args.level}', run mq report --help for valid options.")


def _summary(args: Namespace, run: Run) -> None:
    result = query(args, "0", run)
    table = cli_table(title=f"CLOC @ {run.timestamp_display}")
    table.add_column("Code", justify="center")
    table.add_column("Comment", justify="center")
    table.add_column("Blank", justify="center")
    table.add_column("TOTAL", justify="center")
    table.add_row(
        fmt(result.lines_code, args.options.percentages),
        fmt(result.lines_comment, args.options.percentages),
        fmt(result.lines_blank, args.options.percentages),
        fmt(result.lines_total, args.options.percentages),
    )
    cli_console.print(table)


def _detail(args: Namespace, run: Run, percentage: bool = False) -> None:
    grand_total = query(args, "0", run)
    detail_rows = query(args, "1", run)
    table = cli_table(title=f"CLOC @ {run.timestamp_display}", show_footer=True)
    table.add_column("Directory", justify="left", footer="TOTAL")
    table.add_column("Code", justify="right", footer=fmt(grand_total.lines_code, args.options.percentages))
    table.add_column("Comment", justify="right", footer=fmt(grand_total.lines_comment, args.options.percentages))
    table.add_column("Blank", justify="right", footer=fmt(grand_total.lines_blank, args.options.percentages))
    table.add_column("TOTAL", justify="right", footer=fmt(grand_total.lines_total, args.options.percentages))

    for result in detail_rows:
        table.add_row(
            result.dir,
            fmt(result.lines_code, args.options.percentages),
            fmt(result.lines_comment, args.options.percentages),
            fmt(result.lines_blank, args.options.percentages),
            fmt(result.lines_total, args.options.percentages),
        )
    cli_console.print(table)


def _full(args: Namespace, run: Run) -> None:
    rows, column_totals, grand_total = query(args, "2", run)

    table = cli_table(title=f"CLOC @ {run.timestamp_display}", show_footer=True)
    table.add_column("File", footer="TOTAL")
    table.add_column("Code", justify="right", footer=fmt(column_totals["lines_code"], args.options.percentages))
    table.add_column("Comment", justify="right", footer=fmt(column_totals["lines_comment"], args.options.percentages))
    table.add_column("Blank", justify="right", footer=fmt(column_totals["lines_blank"], args.options.percentages))
    table.add_column("TOTAL", justify="right", footer=fmt(grand_total, args.options.percentages))
    for row in rows:
        table.add_row(
            f"{row.dir}/{row.filename}",
            fmt(row.lines_code, args.options.percentages),
            fmt(row.lines_comment, args.options.percentages),
            fmt(row.lines_blank, args.options.percentages),
            fmt(row.lines_total, args.options.percentages),
        )
    cli_console.print(table)


def _history(args: Namespace, project: Project) -> None:
    timestamps, transposed, grand_totals, roc = query(args, "history", project=project)
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
    if roc["grand_total"]:
        table.add_column("Delta", justify="left", footer=f"{roc['grand_total']:.2f}%")

    for metric, dt_rows in transposed.items():
        row = [metric]
        for timestamp in sorted(timestamps):
            row.append(str(dt_rows[timestamp]))
        if roc[metric]:
            row.append(f"{roc[metric]:+.2f}%")
        table.add_row(*row)

    cli_console.print(table)
