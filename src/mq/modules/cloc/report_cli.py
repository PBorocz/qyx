"""CLI report rendering obo 'cloc' tool."""

from argparse import Namespace
from loguru import logger

from mq.cli import cli_table, cli_console
from mq.modules.models import Project, Run
from mq.modules.cloc import MODULE
from mq.modules.cloc.models import query_detail, query_full, query_history, query_summary
from mq.utils import format_timestamp_headers


def report(args: Namespace) -> None:
    try:
        project = Project.get(Project.path_input == args.project)
    except Project.DoesNotExist:
        logger.error(f"Sorry, we didn't find any data yet for project: {args.project}")
        return None

    # Get most recent Run for simple "current-state" reporting..
    if not (run := Run.get_most_recent(project, MODULE)):
        logger.error("Sorry, we haven't performed a CLOC measurement yet for this project.")
        return None

    if args.last:
        _history(args, project)
    else:
        match args.level.lower():
            case "summary":
                _summary(args, run)
            case "detail":
                _detail(args, run)
            case "full":
                _full(args, run)
            case _:
                logger.warning(f"Sorry, invalid report level provided {args.level}")


def _summary(args: Namespace, run: Run) -> None:
    results = query_summary(run)
    table = cli_table(title=f"CLOC: {run.timestamp_display}")
    table.add_column("Code", justify="right")
    table.add_column("Comment", justify="right")
    table.add_column("Blank", justify="right")
    table.add_column("TOTAL", justify="right")
    table.add_row(
        f"{results.lines_code}",
        f"{results.lines_comment}",
        f"{results.lines_blank}",
        f"{results.lines_total}",
    )
    cli_console.print(table)


def _detail(args: Namespace, run: Run) -> None:
    grand_total = query_summary(run)
    detail_rows = query_detail(run)
    table = cli_table(title=f"CLOC: {run.timestamp_display}", show_footer=True)
    table.add_column("Directory", justify="left", footer="TOTAL")
    table.add_column("Code", justify="right", footer=f"{grand_total.lines_code}")
    table.add_column("Comment", justify="right", footer=f"{grand_total.lines_comment}")
    table.add_column("Blank", justify="right", footer=f"{grand_total.lines_blank}")
    table.add_column("TOTAL", justify="right", footer=f"{grand_total.lines_total}")
    for result in detail_rows:
        table.add_row(
            f"{result.dir}",
            f"{result.lines_code}",
            f"{result.lines_comment}",
            f"{result.lines_blank}",
            f"{result.lines_total}",
        )
    cli_console.print(table)


def _full(args: Namespace, run: Run) -> None:
    rows, column_totals, grand_total = query_full(run)

    table = cli_table(title=f"CLOC: {run.timestamp_display}", show_footer=True)
    table.add_column("File", footer="TOTAL")
    table.add_column("Code", justify="right", footer=str(column_totals["lines_code"]))
    table.add_column("Comment", justify="right", footer=str(column_totals["lines_comment"]))
    table.add_column("Blank", justify="right", footer=str(column_totals["lines_blank"]))
    table.add_column("TOTAL", justify="right", footer=str(grand_total))
    for row in rows:
        table.add_row(
            f"{row.dir}/{row.filename}",
            str(row.lines_code),
            str(row.lines_comment),
            str(row.lines_blank),
            str(row.lines_total),
        )
    cli_console.print(table)


def _history(args: Namespace, project: Project) -> None:
    timestamps, transposed, grand_totals = query_history(project)
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
