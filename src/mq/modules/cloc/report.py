"""Report data obo running 'cloc' tool."""

from collections import defaultdict

from argparse import Namespace
from loguru import logger
from peewee import fn, SqliteDatabase
from rich.console import Console
from rich.table import Table

from mq.modules.models import Project, Run
from mq.modules.cloc import MODULE
from mq.modules.cloc.models import Cloc
from mq.utilities import format_timestamp_headers


def report(args: Namespace) -> None:
    try:
        project = Project.get(Project.source_dir_relative == args.project)
    except Project.DoesNotExist:
        logger.error(f"Sorry, we didn't find any data yet for project: {args.project}")
        return None

    # Get most recent Run for simple "current-state" reporting..
    if not (run := Run.get_most_recent(project, MODULE)):
        logger.error("Sorry, we haven't performed a CLOC measurement yet for this project.")
        return None

    if args.last:
        _report_history(args, project)
    else:
        match args.level.lower():
            case "summary":
                _report_summary(args, run)
            case "detailed":
                _report_detailed(args, run)
            case "full":
                _report_full(args, run)
            case _:
                logger.warning(f"Sorry, invalid report level provided {args.level}")


def _report_history(args: Namespace, project: Project) -> None:
    # Get the args.last number of cloc Runs for this project.
    run_subquery = Run.select(Run.id).where(Run.project_id == project.id, Run.module == MODULE).limit(args.last)

    ################################################################################################
    # Query
    ################################################################################################
    results = (
        Cloc.select(
            Run.timestamp.alias("timestamp"),
            fn.SUM(Cloc.lines_code).alias("total_code"),
            fn.SUM(Cloc.lines_comment).alias("total_comment"),
            fn.SUM(Cloc.lines_blank).alias("total_blank"),
        )
        .join(Run)
        .join(Project)
        .where(Project.id == project.id, Run.id.in_(run_subquery))
        .group_by(Run.timestamp)
        .order_by(Run.timestamp)
        .objects()
    )

    ################################################################################################
    # Transpose (to get timestamps *across* instead of down and calculate grand totals)
    ################################################################################################
    timestamps = [result.timestamp for result in results]
    transposed = defaultdict(lambda: defaultdict(dict))
    grand_totals = defaultdict(int)
    for result in results:
        transposed["Code"][result.timestamp] = result.total_code
        transposed["Comment"][result.timestamp] = result.total_comment
        transposed["Blank"][result.timestamp] = result.total_blank

        # Calculate grand totals for each timestamp as we go
        grand_totals[result.timestamp] += result.total_code + result.total_comment + result.total_blank

    ################################################################################################
    # Render the table
    ################################################################################################
    table = Table(
        title="CLOC Results Over Time",
        show_header=True,
        show_footer=True,
        header_style="bold magenta",
    )

    table.add_column("Metric", justify="left", footer="-")
    for i, header in enumerate(format_timestamp_headers(timestamps)):
        table.add_column(
            header,
            justify="right",
            footer=str(grand_totals[timestamps[i]]),
            footer_style="bold cyan",
        )

    for metric, dt_rows in transposed.items():
        row = [metric]
        for timestamp in timestamps:
            row.append(str(dt_rows[timestamp]))
        table.add_row(*row)

    Console().print(table)


def _report_summary(args: Namespace, run: Run) -> None:
    results = Cloc.select(
        fn.SUM(Cloc.lines_blank).alias("lines_blank"),
        fn.SUM(Cloc.lines_code).alias("lines_code"),
        fn.SUM(Cloc.lines_comment).alias("lines_comment"),
    ).get()
    table = Table(
        title=f"cloc: {run.timestamp_display}",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Code", justify="right")
    table.add_column("Comment", justify="right")
    table.add_column("Blank", justify="right")
    table.add_row(
        f"{results.lines_code}",
        f"{results.lines_comment}",
        f"{results.lines_blank}",
    )
    Console().print(table)


def _report_detailed(args: Namespace, run: Run) -> None:
    results = (
        Cloc.select(
            Cloc.dir,
            fn.SUM(Cloc.lines_blank).alias("lines_blank"),
            fn.SUM(Cloc.lines_code).alias("lines_code"),
            fn.SUM(Cloc.lines_comment).alias("lines_comment"),
        )
        .group_by(Cloc.dir)
        .order_by(Cloc.dir)
    )
    table = Table(
        title=f"cloc: {run.timestamp_display}",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Directory", justify="left")
    table.add_column("Code", justify="right")
    table.add_column("Comment", justify="right")
    table.add_column("Blank", justify="right")
    for result in results:
        table.add_row(
            f"{result.dir}",
            f"{result.lines_code}",
            f"{result.lines_comment}",
            f"{result.lines_blank}",
        )
    Console().print(table)


def _report_full(args: Namespace, run: Run) -> None:
    rows = Cloc.select().where(Cloc.run_id == run).order_by(Cloc.dir, Cloc.filename)
    sums = defaultdict(int)
    for row in rows:
        sums["blank"] += row.lines_blank
        sums["comment"] += row.lines_comment
        sums["code"] += row.lines_code

    table = Table(
        title=f"cloc: {run.timestamp_display}",
        show_header=True,
        show_footer=True,
        header_style="bold magenta",
    )
    table.add_column("File", footer="Total")
    table.add_column("Code", justify="right", footer=str(sums["code"]))
    table.add_column("Comment", justify="right", footer=str(sums["comment"]))
    table.add_column("Blank", justify="right", footer=str(sums["blank"]))
    for row in rows:
        table.add_row(
            f"{row.dir}/{row.filename}",
            str(row.lines_code),
            str(row.lines_comment),
            str(row.lines_blank),
        )
    Console().print(table)
