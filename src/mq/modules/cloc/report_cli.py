"""CLI report rendering obo 'cloc' tool."""

import logging
from argparse import Namespace

from mq.cli import cli_table, cli_console
from mq.modules import format_int_or_percentage as fmt
from mq.modules.base import Project, Request, Scan
from mq.modules.cloc import MODULE
from mq.modules.cloc.models import query
from mq.utils import format_timestamp_headers

log = logging.getLogger(__name__)


def report(args: Namespace) -> None:
    if not (project := Project.get_by_identifier(args.project)):
        log.error(f"Sorry, we didn't find any data yet for project: {args.project}")
        return None

    # Get most recent Request for simple "current-state" reporting..
    if not (request := Request.get_most_recent(project, MODULE)):
        log.error("Sorry, we haven't performed a CLOC measurement yet for this project.")
        return None

    # Get most recent Scan for simple "current-state" reporting..
    if not (scan := Scan.get_most_recent(request, MODULE)):
        log.error("Sorry, we haven't performed a CLOC measurement yet for this project.")
        return None

    match args.level.lower():
        case "0":
            _summary(args, scan)
        case "1":
            _detail(args, scan)
        case "2":
            _full(args, scan)
        case "h" | "history":
            _history(args, project, request)
        case _:
            log.warning(f"Sorry, invalid report level: '{args.level}', run mq report --help for valid options.")


def _summary(args: Namespace, scan: Scan) -> None:
    result = query(args, "0", scan=scan)
    table = cli_table(title=f"CLOC @ {scan.timestamp_display()}")
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


def _detail(args: Namespace, scan: Scan, percentage: bool = False) -> None:
    grand_total = query(args, "0", scan=scan)
    detail_rows = query(args, "1", scan=scan)
    table = cli_table(title=f"CLOC @ {scan.timestamp_display()}", show_footer=True)
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


def _full(args: Namespace, scan: Scan) -> None:
    rows, column_totals, grand_total = query(args, "2", scan=scan)

    table = cli_table(title=f"CLOC @ {scan.timestamp_display()}", show_footer=True)
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


def _history(args: Namespace, project: Project, request: Request) -> None:
    timestamps, rows, transposed, grand_totals, roc, adgs = query(args, "history", project=project, request=request)
    timestamps_formatted = format_timestamp_headers(timestamps)
    if len(timestamps) <= 20:
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
            table.add_column("Delta", justify="left", footer=f"{roc['grand_total']:,.2f}%")

        for metric, dt_rows in transposed.items():
            row = [metric]
            for timestamp in sorted(timestamps):
                row.append(str(dt_rows[timestamp]))
            if roc[metric]:
                row.append(f"{roc[metric]:+.2f}%")
            table.add_row(*row)
    else:
        table = cli_table(title="CLOC Results Over Time", show_footer=True)
        table.add_column("", justify="left", footer="Average Daily Growth")
        table.add_column("Code", justify="right", footer=f"{adgs['total_code']:,.0f}")
        table.add_column("Comment", justify="right", footer=f"{adgs['total_comment']:,.0f}")
        table.add_column("Blank", justify="right", footer=f"{adgs['total_blank']:,.0f}")
        for row in rows:
            t_row = [
                timestamps_formatted[row.timestamp],
                f"{row.total_code:,d}",
                f"{row.total_comment:,d}",
                f"{row.total_blank:,d}",
            ]
            table.add_row(*t_row)

    cli_console.print(table)
