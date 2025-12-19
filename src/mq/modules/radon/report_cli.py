"""..."""

import sys
from argparse import Namespace
from collections import defaultdict

from loguru import logger
from peewee import fn
from rich.console import Console
from rich.table import Table

from mq.modules.models import Project, Run
from mq.modules.radon import MODULE
from mq.modules.radon.models import RadonCc, RadonHal, RadonHalFunction, RadonMi, RadonRaw

RADON_SUB_MODULES = ("raw", "mi", "hal", "cc")


def report(args: Namespace) -> None:
    try:
        project = Project.get(path_input=args.project)
    except Project.DoesNotExist:
        logger.error(f"Sorry, we didn't find any data yet for project: {args.project}")
        return None

    if args.last:
        ...
        # TODO: Implement me!!
        raise RuntimeError("TODO!")
        # _report_history(args, project)
    else:
        if args.sub_module:
            if not (run := Run.get_most_recent(project, MODULE, args.sub_module)):
                logger.info(f"Sorry, we haven't performed a {args.sub_module} measurement yet for this project.")
            _dispatch_level_submodule(args, args.sub_module, run)
        else:
            for sub_module in RADON_SUB_MODULES:
                # Get most recent Run for simple "current-state" reporting..
                if not (run := Run.get_most_recent(project, MODULE, sub_module)):
                    logger.info(f"Sorry, we haven't performed a {sub_module} measurement yet for this project.")
                    continue
                _dispatch_level_submodule(args, sub_module, run)


def _dispatch_level_submodule(args: Namespace, sub_module: str, run: Run) -> None:
    """Dispatch to the report method using the report level and sub_module requested."""
    current_module = sys.modules[__name__]
    method_name = f"_{args.level}_{sub_module}"
    if method := getattr(current_module, method_name):
        method(args, run)
    else:
        logger.warning(f"Sorry, unable to report yet on level='{args.level}' & sub_module='{args.sub_module}'.")


################################################################################################
# Summary methods
################################################################################################
def _summary_raw(args: Namespace, run: Run) -> None:
    rows = RadonRaw.select(
        fn.SUM(RadonRaw.loc).alias("loc"),
        fn.SUM(RadonRaw.lloc).alias("lloc"),
        fn.SUM(RadonRaw.sloc).alias("sloc"),
        fn.SUM(RadonRaw.comments).alias("comments"),
        fn.SUM(RadonRaw.multi).alias("multi"),
        fn.SUM(RadonRaw.blank).alias("blank"),
        fn.SUM(RadonRaw.single_comments).alias("single_comments"),
    ).where(RadonRaw.run == run.id)

    table = Table(
        title=f"RADON-RAW: {run.timestamp_display}",
        title_style="bold green",
        title_justify="left",
        show_header=True,
        header_style="bold magenta",
    )
    # fmt: off
    table.add_column("LOC"             , justify="right")
    table.add_column("LLOC"            , justify="right")
    table.add_column("SLOC"            , justify="right")
    table.add_column("Comments"        , justify="right")
    table.add_column("Multi"           , justify="right")
    table.add_column("Blank"           , justify="right")
    table.add_column("Single Comments" , justify="right")
    # fmt: on
    for row in rows:
        table.add_row(
            f"{row.loc:,}",
            f"{row.lloc:,}",
            f"{row.sloc:,}",
            f"{row.comments:,}",
            f"{row.multi:,}",
            f"{row.blank:,}",
            f"{row.single_comments:,}",
        )
    Console().print(table)


def _summary_hal(args: Namespace, run: Run) -> None:
    rows = (
        RadonHal.select(
            RadonHal.dir,
            fn.AVG(RadonHal.h1).alias("h1"),
            fn.AVG(RadonHal.h2).alias("h2"),
            fn.AVG(RadonHal.N1).alias("N1"),
            fn.AVG(RadonHal.N2).alias("N2"),
            fn.AVG(RadonHal.program_vocabulary).alias("program_vocabulary"),
            fn.AVG(RadonHal.program_length).alias("program_length"),
            fn.AVG(RadonHal.calculated_length).alias("calculated_length"),
            fn.AVG(RadonHal.volume).alias("volume"),
            fn.AVG(RadonHal.difficulty).alias("difficulty"),
            fn.AVG(RadonHal.effort).alias("effort"),
            fn.AVG(RadonHal.time).alias("time"),
            fn.AVG(RadonHal.bugs).alias("bugs"),
        )
        .group_by(RadonHal.dir)
        .where(RadonHal.run == run.id)
        .order_by(RadonHal.dir)
    )
    # Calculate mean metric values
    means = {}
    for attr in RadonHal.attributes():
        values = [getattr(row, attr) for row in rows]
        means[attr] = sum(values) / len(values) if values else None

    table = Table(
        title=f"RADON-HAL: {run.timestamp_display}",
        title_style="bold green",
        title_justify="left",
        show_header=True,
        show_footer=True,
        header_style="bold magenta",
    )
    # fmt: off
    table.add_column("Directory"          , justify="left" , footer="Means")
    table.add_column("h1"                 , justify="right", footer=f"{means['h1']:.2f}")
    table.add_column("h2"                 , justify="right", footer=f"{means['h2']:.2f}")
    table.add_column("N1"                 , justify="right", footer=f"{means['N1']:.2f}")
    table.add_column("N2"                 , justify="right", footer=f"{means['N2']:.2f}")
    table.add_column("Program Vocabulary" , justify="right", footer=f"{means['program_vocabulary']:.2f}")
    table.add_column("Program Length"     , justify="right", footer=f"{means['program_length']:.2f}")
    table.add_column("Calculated Length"  , justify="right", footer=f"{means['calculated_length']:.2f}")
    table.add_column("Volume"             , justify="right", footer=f"{means['volume']:.2f}")
    table.add_column("Difficulty"         , justify="right", footer=f"{means['difficulty']:.2f}")
    table.add_column("Effort"             , justify="right", footer=f"{means['effort']:.2f}")
    table.add_column("Time"               , justify="right", footer=f"{means['time']:.2f}")
    table.add_column("Bugs"               , justify="right", footer=f"{means['bugs']:.2f}")
    # fmt: on
    for row in rows:
        table.add_row(
            row.dir,
            f"{row.h1:.2f}",
            f"{row.h2:.2f}",
            f"{row.N1:.2f}",
            f"{row.N2:.2f}",
            f"{row.program_vocabulary:.2f}",
            f"{row.program_length:.2f}",
            f"{row.calculated_length:.2f}",
            f"{row.volume:.2f}",
            f"{row.difficulty:.2f}",
            f"{row.effort:.2f}",
            f"{row.time:.2f}",
            f"{row.bugs:.2f}",
        )
    Console().print(table)


def _summary_mi(args: Namespace, run: Run) -> None:
    row = RadonMi.select(fn.AVG(RadonMi.mi).alias("mi_mean")).where(RadonMi.run == run.id).get()
    table = Table(
        title=f"RADON-MI: {run.timestamp_display}",
        title_style="bold green",
        title_justify="left",
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
        .where(RadonCc.run == run.id)
        .group_by(RadonCc.entity_type)
        .order_by(fn.COUNT(RadonCc.id).desc())
    )
    table = Table(
        title=f"RADON-CC: {run.timestamp_display}",
        title_style="bold green",
        title_justify="left",
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
def _detail_raw(args: Namespace, run: Run) -> None:
    rows = (
        RadonRaw.select(
            RadonRaw.dir,
            fn.SUM(RadonRaw.loc).alias("loc"),
            fn.SUM(RadonRaw.lloc).alias("lloc"),
            fn.SUM(RadonRaw.sloc).alias("sloc"),
            fn.SUM(RadonRaw.comments).alias("comments"),
            fn.SUM(RadonRaw.multi).alias("multi"),
            fn.SUM(RadonRaw.blank).alias("blank"),
            fn.SUM(RadonRaw.single_comments).alias("single_comments"),
        )
        .where(RadonRaw.run == run.id)
        .group_by(RadonRaw.dir)
        .order_by(RadonRaw.dir)
    )

    # Calculate grand totals
    totals = defaultdict(int)
    for row in rows:
        for attr in ("loc", "lloc", "sloc", "comments", "multi", "blank", "single_comments"):
            totals[attr] += getattr(row, attr)

    table = Table(
        title=f"RADON-RAW: {run.timestamp_display}",
        title_style="bold green",
        show_header=True,
        show_footer=True,
        header_style="bold magenta",
    )
    # fmt: off
    table.add_column("Directory"       , justify="left")
    table.add_column("LOC"             , justify="right", footer=f"{totals['loc'             ]:,}")
    table.add_column("LLOC"            , justify="right", footer=f"{totals['lloc'            ]:,}")
    table.add_column("SLOC"            , justify="right", footer=f"{totals['sloc'            ]:,}")
    table.add_column("Comments"        , justify="right", footer=f"{totals['comments'        ]:,}")
    table.add_column("Multi"           , justify="right", footer=f"{totals['multi'           ]:,}")
    table.add_column("Blank"           , justify="right", footer=f"{totals['blank'           ]:,}")
    table.add_column("Single Comments" , justify="right", footer=f"{totals['single_comments' ]:,}")
    # fmt: on
    for row in rows:
        table.add_row(
            row.dir,
            f"{row.loc:,}",
            f"{row.lloc:,}",
            f"{row.sloc:,}",
            f"{row.comments:,}",
            f"{row.multi:,}",
            f"{row.blank:,}",
            f"{row.single_comments:,}",
        )
    Console().print(table)


def _detail_hal(args: Namespace, run: Run) -> None:
    rows = RadonHal.select().where(RadonHal.run == run.id).order_by(RadonHal.dir, RadonHal.filename)

    # Calculate means
    means = {}
    for attr in RadonHal.attributes():
        values = [getattr(row, attr) for row in rows]
        means[attr] = sum(values) / len(values) if values else None

    table = Table(
        title=f"RADON-HAL: {run.timestamp_display}",
        title_style="bold green",
        show_header=True,
        show_footer=True,
        header_style="bold magenta",
    )
    # fmt: off
    table.add_column("File"               , justify="left" , footer="Means")
    table.add_column("h1"                 , justify="right", footer=f"{means['h1']:.2f}")
    table.add_column("h2"                 , justify="right", footer=f"{means['h2']:.2f}")
    table.add_column("N1"                 , justify="right", footer=f"{means['N1']:.2f}")
    table.add_column("N2"                 , justify="right", footer=f"{means['N2']:.2f}")
    table.add_column("Program Vocabulary" , justify="right", footer=f"{means['program_vocabulary']:.2f}")
    table.add_column("Program Length"     , justify="right", footer=f"{means['program_length']:.2f}")
    table.add_column("Calculated Length"  , justify="right", footer=f"{means['calculated_length']:.2f}")
    table.add_column("Volume"             , justify="right", footer=f"{means['volume']:.2f}")
    table.add_column("Difficulty"         , justify="right", footer=f"{means['difficulty']:.2f}")
    table.add_column("Effort"             , justify="right", footer=f"{means['effort']:.2f}")
    table.add_column("Time"               , justify="right", footer=f"{means['time']:.2f}")
    table.add_column("Bugs"               , justify="right", footer=f"{means['bugs']:.2f}")
    # fmt: on
    for row in rows:
        table.add_row(
            f"{row.dir}/{row.filename}",
            f"{row.h1:,}",
            f"{row.h2:,}",
            f"{row.N1:,}",
            f"{row.N2:,}",
            f"{row.program_vocabulary:,}",
            f"{row.program_length:,}",
            f"{row.calculated_length:,}",
            f"{row.volume:.2f}",
            f"{row.difficulty:.2f}",
            f"{row.effort:.2f}",
            f"{row.time:.2f}",
            f"{row.bugs:.2f}",
        )
    Console().print(table)


def _detail_mi(args: Namespace, run: Run) -> None:
    rows = (
        RadonMi.select(RadonMi.dir, fn.AVG(RadonMi.mi).alias("mi_mean"))
        .where(RadonMi.run == run.id)
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
        title=f"RADON-MI: {run.timestamp_display}",
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
        .where(RadonCc.run == run.id)
        .group_by(RadonCc.dir, RadonCc.entity_type)
        .order_by(RadonCc.dir, RadonCc.entity_type)
    )
    table = Table(
        title=f"RADON-CC: {run.timestamp_display}",
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
def _full_raw(args: Namespace, run: Run) -> None:
    rows = RadonRaw.select().where(RadonRaw.run == run.id).order_by(RadonRaw.dir, RadonRaw.filename)

    # Calculate grand totals
    totals = defaultdict(int)
    for row in rows:
        for attr in ("loc", "lloc", "sloc", "comments", "multi", "blank", "single_comments"):
            totals[attr] += getattr(row, attr)

    table = Table(
        title=f"RADON-RAW: {run.timestamp_display}",
        title_style="bold green",
        show_header=True,
        show_footer=True,
        header_style="bold magenta",
    )
    # fmt: off
    table.add_column("Directory"       , justify="left")
    table.add_column("File"            , justify="left")
    table.add_column("LOC"             , justify="right", footer=f"{totals['loc'             ]:,}")
    table.add_column("LLOC"            , justify="right", footer=f"{totals['lloc'            ]:,}")
    table.add_column("SLOC"            , justify="right", footer=f"{totals['sloc'            ]:,}")
    table.add_column("Comments"        , justify="right", footer=f"{totals['comments'        ]:,}")
    table.add_column("Multi"           , justify="right", footer=f"{totals['multi'           ]:,}")
    table.add_column("Blank"           , justify="right", footer=f"{totals['blank'           ]:,}")
    table.add_column("Single Comments" , justify="right", footer=f"{totals['single_comments' ]:,}")
    # fmt: on
    for row in rows:
        table.add_row(
            row.dir,
            row.filename,
            f"{row.loc:,}",
            f"{row.lloc:,}",
            f"{row.sloc:,}",
            f"{row.comments:,}",
            f"{row.multi:,}",
            f"{row.blank:,}",
            f"{row.single_comments:,}",
        )
    Console().print(table)


def _full_hal(args: Namespace, run: Run) -> None:
    rows = (
        RadonHalFunction.select(
            RadonHal.dir,
            RadonHal.filename,
            RadonHalFunction.name,
            RadonHalFunction.h1,
            RadonHalFunction.h2,
            RadonHalFunction.N1,
            RadonHalFunction.N2,
            RadonHalFunction.program_vocabulary,
            RadonHalFunction.program_length,
            RadonHalFunction.calculated_length,
            RadonHalFunction.volume,
            RadonHalFunction.difficulty,
            RadonHalFunction.effort,
            RadonHalFunction.time,
            RadonHalFunction.bugs,
        )
        .join(RadonHal)
        .where(RadonHal.run == run.id)
        .order_by(RadonHal.dir, RadonHal.filename, RadonHalFunction.name)
        .objects()
    )
    # Calculate mean metric values
    means = {}
    for attr in RadonHal.attributes():
        values = [getattr(row, attr) for row in rows]
        means[attr] = sum(values) / len(values) if values else None

    table = Table(
        title=f"RADON-HAL: {run.timestamp_display}",
        title_style="bold green",
        show_header=True,
        show_footer=True,
        header_style="bold magenta",
    )
    # fmt: off
    table.add_column("File"               , justify="left" , footer="Means")
    table.add_column("Name"               , justify="left")
    table.add_column("h1"                 , justify="right", footer=f"{means['h1']:.2f}")
    table.add_column("h2"                 , justify="right", footer=f"{means['h2']:.2f}")
    table.add_column("N1"                 , justify="right", footer=f"{means['N1']:.2f}")
    table.add_column("N2"                 , justify="right", footer=f"{means['N2']:.2f}")
    table.add_column("Program Vocabulary" , justify="right", footer=f"{means['program_vocabulary']:.2f}")
    table.add_column("Program Length"     , justify="right", footer=f"{means['program_length']:.2f}")
    table.add_column("Calculated Length"  , justify="right", footer=f"{means['calculated_length']:.2f}")
    table.add_column("Volume"             , justify="right", footer=f"{means['volume']:.2f}")
    table.add_column("Difficulty"         , justify="right", footer=f"{means['difficulty']:.2f}")
    table.add_column("Effort"             , justify="right", footer=f"{means['effort']:.2f}")
    table.add_column("Time"               , justify="right", footer=f"{means['time']:.2f}")
    table.add_column("Bugs"               , justify="right", footer=f"{means['bugs']:.2f}")
    # fmt: on
    for row in rows:
        table.add_row(
            f"{row.dir}/{row.filename}",
            row.name,
            f"{row.h1:,}",
            f"{row.h2:,}",
            f"{row.N1:,}",
            f"{row.N2:,}",
            f"{row.program_vocabulary:,}",
            f"{row.program_length:,}",
            f"{row.calculated_length:,}",
            f"{row.volume:.2f}",
            f"{row.difficulty:.2f}",
            f"{row.effort:.2f}",
            f"{row.time:.2f}",
            f"{row.bugs:.2f}",
        )
    Console().print(table)


def _full_mi(args: Namespace, run: Run) -> None:
    rows = RadonMi.select().where(RadonMi.run == run.id).order_by(RadonMi.mi.asc(), RadonMi.dir, RadonMi.filename)

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
        title=f"RADON-MI: {run.timestamp_display}",
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
        .where(RadonCc.run == run.id)
        .group_by(RadonCc.dir, RadonCc.filename, RadonCc.entity_type)
        .order_by(RadonCc.dir, RadonCc.filename, RadonCc.entity_type)
    )
    table = Table(
        title=f"RADON-CC: {run.timestamp_display}",
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
