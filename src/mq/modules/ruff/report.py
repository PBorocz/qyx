"""..."""

from argparse import Namespace
from collections import defaultdict
from loguru import logger
from peewee import fn, SqliteDatabase
from rich.console import Console
from rich.table import Table

from mq.modules.models import Project, Run
from mq.modules.ruff import MODULE
from mq.modules.ruff.models import Ruff
from mq.utilities import format_timestamp_headers, remove_common_prefixes


def report(args: Namespace) -> None:
    try:
        project = Project.get(source_dir_relative=args.project)
    except Project.DoesNotExist:
        logger.error(f"Sorry, we didn't find any data yet for project: {args.project}")
        return None

    # Get most recent Run for simple "current-state" reporting..
    if not (run := Run.get_most_recent(project, MODULE)):
        logger.error(f"Sorry, we haven't performed a {MODULE.upper()} measurement yet for this project.")
        return None

    if args.last:
        _report_history(args, project)
    else:
        match args.level.lower():
            case "summary":
                _report_summary(args, run)
            case "detailed":
                _report_detailed(args, run)
            case _:
                logger.warning(f"Sorry, invalid report level {args.level}, must be one of 'summary' or 'detailed'.")


def _report_summary(args: Namespace, run: Run) -> None:
    results = (
        Ruff.select(Ruff.rule_code, Ruff.message, fn.COUNT(Ruff.id).alias("count"))
        .where(Ruff.run_id == run)
        .group_by(Ruff.rule_code)
        .order_by(fn.COUNT(Ruff.id).desc())
    )
    table = Table(
        title=f"ruff: {run.timestamp_display}",
        title_style="bold green",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Rule")
    table.add_column("Count", justify="center")
    table.add_column("Message")
    for result in results:
        table.add_row(result.rule_code, str(result.count), result.message)
    Console().print(table)


def _report_detailed(args: Namespace, run: Run) -> None:
    rows = Ruff.select().where(Ruff.run_id == run).order_by(Ruff.filename, Ruff.rule_code)
    foobar = 1
    rows = remove_common_prefixes(rows)
    table = Table(
        title=f"ruff: {run.timestamp_display}",
        title_style="bold green",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Rule")
    table.add_column("File (line)")
    table.add_column("Message")
    for row in rows:
        table.add_row(row.rule_code, f"{row.filename} [{row.line}] ", row.message)
    Console().print(table)


def _report_history(args: Namespace, project: Project) -> None:
    """Report on the args.last number of runs "across"."""
    runs = Run.select(Run.id).where(Run.project_id == project.id, Run.module == MODULE).limit(args.last)

    ################################################################################################
    # Query
    ################################################################################################
    rows = (
        Ruff.select(
            Run.timestamp.alias("timestamp"),
            Ruff.rule_code.alias("rule_code"),
            Ruff.message.alias("message"),
        )
        .where(Project.id == project.id, Run.id.in_(runs))
        .join(Run)
        .join(Project)
        .order_by(Run.timestamp)
        .objects()
    )
    messages = {row.rule_code: row.message for row in rows}

    ################################################################################################
    # Transpose (to get timestamps *across* instead of down and calculate grand totals)
    ################################################################################################
    transposed = defaultdict(lambda: defaultdict(int))
    grand_totals = defaultdict(int)
    for row in rows:
        transposed[row.rule_code][row.timestamp] += 1
        grand_totals[row.timestamp] += 1

    ################################################################################################
    # Render the table
    ################################################################################################
    table = Table(
        title="RUFF Results Over Time",
        show_header=True,
        show_footer=True,
        header_style="bold magenta",
    )

    table.add_column("Rule", justify="left", footer="-")
    table.add_column("Message", justify="left", footer="-")
    timestamps = list({row.timestamp for row in rows})
    timestamps_formatted = format_timestamp_headers(timestamps)
    for i, header in enumerate(timestamps_formatted):
        table.add_column(
            header,
            justify="right",
            footer=str(grand_totals[timestamps[i]]),
            footer_style="bold cyan",
        )

    for rule_code, dt_rows in transposed.items():
        row = [rule_code, messages[rule_code]]
        for timestamp in timestamps:
            row.append(str(dt_rows[timestamp]))
        table.add_row(*row)

    Console().print(table)
