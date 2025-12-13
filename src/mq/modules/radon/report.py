"""..."""

import sys
from argparse import Namespace
from loguru import logger
from peewee import fn, SqliteDatabase
from rich.console import Console
from rich.table import Table

from mq.modules.models import Project, Run
from mq.modules.radon import MODULE
from mq.modules.radon.models import RadonCc, RadonHal, RadonHalFunction, RadonMi, RadonRaw
from mq.utilities import remove_common_prefixes


def report(args: Namespace) -> None:
    try:
        project = Project.get(source_dir_relative=args.project)
    except Project.DoesNotExist:
        logger.error(f"Sorry, we didn't find any data yet for project: {args.project}")
        return None

    # Get most recent Run for simple "current-state" reporting..
    if not (run := Run.get_most_recent(project, MODULE, args.sub_module)):
        logger.error(f"Sorry, we haven't performed a {MODULE.upper()} measurement yet for this project.")
        return None

    if args.last:
        ...
        # _report_history(args, project)
    else:
        # Dispatch "intelligently"...
        _dispatch(args, run)


def _dispatch(args: Namespace, run: Run) -> None:
    # Get current module
    current_module = sys.modules[__name__]

    # Construct method name
    method_name = f"_{args.level}_{args.sub_module}"

    # Get the method if it exists
    if hasattr(current_module, method_name):
        method = getattr(current_module, method_name)
        method(args, run)
    else:
        logger.warning(f"Sorry, unable to report yet on level='{args.level}' & sub_module='{args.sub_module}'.")


def _summary_cc(args: Namespace, run: Run) -> None:
    results = (
        RadonCc.select(
            RadonCc.entity_type.alias("entity_type"),
            fn.COUNT(RadonCc.id).alias("count"),
        )
        .where(RadonCc.run_id == run.id)
        .group_by(RadonCc.entity_type)
        .order_by(fn.COUNT(RadonCc.id).desc())
        .objects()
    )
    table = Table(
        title=f"Radon-{args.sub_module.upper()}: {run.timestamp_display}",
        title_style="bold green",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Entity Type")
    table.add_column("Count", justify="center")
    for result in results:
        table.add_row(result.entity_type, str(result.count))
    Console().print(table)


def _detailed_cc(args: Namespace, run: Run) -> None:
    results = (
        RadonCc.select(
            RadonCc.dir,
            RadonCc.entity_type,
            fn.COUNT(RadonCc.id).alias("count"),
        )
        .where(RadonCc.run_id == run.id)
        .group_by(RadonCc.dir, RadonCc.entity_type)
        .order_by(RadonCc.dir, RadonCc.entity_type)
    )
    table = Table(
        title=f"Radon-{args.sub_module.upper()}: {run.timestamp_display}",
        title_style="bold green",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Directory", justify="left")
    table.add_column("Entity Type", justify="left")
    table.add_column("Count", justify="center")
    for result in results:
        table.add_row(
            result.dir,
            result.filename,
            result.entity_type,
            str(result.count),
        )
    Console().print(table)


def _full_cc(args: Namespace, run: Run) -> None:
    results = (
        RadonCc.select(
            RadonCc.dir,
            RadonCc.filename,
            RadonCc.entity_type,
            fn.COUNT(RadonCc.id).alias("count"),
        )
        .where(RadonCc.run_id == run.id)
        .group_by(RadonCc.dir, RadonCc.filename, RadonCc.entity_type)
        .order_by(RadonCc.dir, RadonCc.filename, RadonCc.entity_type)
    )
    table = Table(
        title=f"Radon-{args.sub_module.upper()}: {run.timestamp_display}",
        title_style="bold green",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Directory", justify="left")
    table.add_column("File", justify="left")
    table.add_column("Entity Type", justify="left")
    table.add_column("Count", justify="center")
    for result in results:
        table.add_row(
            result.dir,
            result.filename,
            result.entity_type,
            str(result.count),
        )
    Console().print(table)
