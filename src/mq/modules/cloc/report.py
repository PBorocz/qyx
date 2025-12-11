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


def report(args: Namespace, db: SqliteDatabase) -> None:
    try:
        project = Project.get(Project.source_dir == args.project)
    except Project.DoesNotExist:
        logger.error(f"Sorry, we didn't find any data yet for project: {args.project}")
        return None

    # Get most recent Run for simple "current-state" reporting..
    run = Run.select().order_by(Run.timestamp.desc()).where(Run.project_id == project.id, Run.module == MODULE).first()
    if not run:
        logger.error("Sorry, we haven't performed a CLOC measurement yet for this project.")
        return None

    match args.verbosity:
        case 0:
            _report_simple(args, run)
        case 1:
            _report_verbose(args, run)
        case _:
            logger.info("Sorry, for now we only support verbosity of '0' and '1'")


def _report_simple(args: Namespace, run: Run) -> None:
    results = Cloc.select(
        fn.SUM(Cloc.lines_blank).alias("lines_blank"),
        fn.SUM(Cloc.lines_code).alias("lines_code"),
        fn.SUM(Cloc.lines_comment).alias("lines_comment"),
    ).get()
    table = Table(
        title=f"cloc: {run.timestamp_local}",
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


def _report_verbose(args: Namespace, run: Run) -> None:
    rows = Cloc.select().where(Cloc.run_id == run).order_by(Cloc.dir, Cloc.filename)
    sums = defaultdict(int)
    for row in rows:
        sums["blank"] += row.lines_blank
        sums["comment"] += row.lines_comment
        sums["code"] += row.lines_code

    table = Table(
        title=f"cloc: {run.timestamp_local}",
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
