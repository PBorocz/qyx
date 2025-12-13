"""..."""

import sys
from argparse import Namespace

from loguru import logger
from peewee import fn
from rich.console import Console
from rich.table import Table

from mq.modules.models import Project, Run
from mq.modules.radon import MODULE
from mq.modules.radon.models import RadonCc, RadonHal, RadonHalFunction, RadonMi, RadonRaw


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
        _dispatch_level_submodule(args, run)


def _dispatch_level_submodule(args: Namespace, run: Run) -> None:
    """Dispatch to the report method using the report level and sub_module requested."""
    current_module = sys.modules[__name__]
    method_name = f"_{args.level}_{args.sub_module}"
    if hasattr(current_module, method_name):
        method = getattr(current_module, method_name)
        method(args, run)
    else:
        logger.warning(f"Sorry, unable to report yet on level='{args.level}' & sub_module='{args.sub_module}'.")


################################################################################################
# Summary methods
################################################################################################
def _summary_raw(args: Namespace, run: Run) -> None: ...


def _summary_hal(args: Namespace, run: Run) -> None: ...


def _summary_mi(args: Namespace, run: Run) -> None:
    row = RadonMi.select(fn.AVG(RadonMi.mi).alias("mi_mean")).where(RadonMi.run_id == run.id).get()
    table = Table(
        title=f"Radon-{args.sub_module.upper()}: {run.timestamp_display}",
        title_style="bold green",
        show_header=False,
    )
    table.add_column("_", style="bold magenta")
    table.add_column("_", style="bold magenta")
    table.add_row(
        "Composite Maintainability Score",
        f"{row.mi_mean:.2f}",
    )
    Console().print(table)


def _summary_cc(args: Namespace, run: Run) -> None:
    rows = (
        RadonCc.select(
            RadonCc.entity_type.alias("entity_type"),
            fn.COUNT(RadonCc.id).alias("count"),
        )
        .where(RadonCc.run_id == run.id)
        .group_by(RadonCc.entity_type)
        .order_by(fn.COUNT(RadonCc.id).desc())
    )
    table = Table(
        title=f"Radon-{args.sub_module.upper()}: {run.timestamp_display}",
        title_style="bold green",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Entity Type")
    table.add_column("Count", justify="center")
    for row in rows:
        table.add_row(row.entity_type, str(row.count))
    Console().print(table)


################################################################################################
# Detail methods
################################################################################################
def _detail_raw(args: Namespace, run: Run) -> None: ...


def _detail_hal(args: Namespace, run: Run) -> None: ...


def _detail_mi(args: Namespace, run: Run) -> None:
    rows = (
        RadonMi.select(RadonMi.dir, fn.AVG(RadonMi.mi).alias("mi_mean"))
        .where(RadonMi.run_id == run.id)
        .order_by(fn.AVG(RadonMi.mi).asc(), RadonMi.dir)
        .group_by(RadonMi.dir)
    )

    # Calculate the mean mean maintainability index
    mi_mean_s = [row.mi_mean for row in rows]
    if mi_mean_s:
        mean_mi_mean = sum(mi_mean_s) / len(mi_mean_s)
        mean_mi_mean_footer = f"{mean_mi_mean:.2f}"
        show_footer = True
    else:
        mean_mi_mean_footer = ""
        show_footer = False

    table = Table(
        title=f"Radon-{args.sub_module.upper()}: {run.timestamp_display}",
        title_style="bold green",
        show_header=True,
        show_footer=show_footer,
        header_style="bold magenta",
    )
    table.add_column("Directory", justify="left", footer="Composite Maintainability")
    table.add_column("Maintainability Index", justify="right", footer=mean_mi_mean_footer)
    for row in rows:
        table.add_row(
            row.dir,
            f"{row.mi_mean:.2f}",
        )
    Console().print(table)


def _detail_cc(args: Namespace, run: Run) -> None:
    rows = (
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
    for row in rows:
        table.add_row(
            row.dir,
            row.filename,
            row.entity_type,
            str(row.count),
        )
    Console().print(table)


################################################################################################
# "Full" methods
################################################################################################
def _full_raw(args: Namespace, run: Run) -> None: ...


def _full_hal(args: Namespace, run: Run) -> None: ...


def _full_mi(args: Namespace, run: Run) -> None:
    rows = RadonMi.select().where(RadonMi.run_id == run.id).order_by(RadonMi.mi.asc(), RadonMi.dir, RadonMi.filename)

    # Calculate the average maintainability index
    mi_s = [row.mi for row in rows]
    if mi_s:
        avg_mi = sum(mi_s) / len(mi_s)
        avg_footer = f"{avg_mi:.2f}"
        show_footer = True
    else:
        avg_footer = ""
        show_footer = False

    table = Table(
        title=f"Radon-{args.sub_module.upper()}: {run.timestamp_display}",
        title_style="bold green",
        show_header=True,
        show_footer=show_footer,
        header_style="bold magenta",
    )
    table.add_column("Directory", justify="left", footer="Composite Maintainability")
    table.add_column("Filename", justify="left", footer="(simple mean)")
    table.add_column("Maintainability Index", justify="right", footer=avg_footer)
    table.add_column("Rank", justify="center")
    for row in rows:
        table.add_row(
            row.dir,
            row.filename,
            f"{row.mi:.2f}",
            row.rank,
        )
    Console().print(table)


def _full_cc(args: Namespace, run: Run) -> None:
    rows = (
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
    for row in rows:
        table.add_row(
            row.dir,
            row.filename,
            row.entity_type,
            str(row.count),
        )
    Console().print(table)
