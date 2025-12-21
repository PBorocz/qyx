"""..."""

import logging
import sys
from argparse import Namespace
from collections import defaultdict

from mq.cli import cli_console, cli_table
from mq.modules.base import Project, Run
from mq.modules.radon import COLORS, MODULE
from mq.modules.radon.models import (
    RadonHal,
    query_cc,
    query_hal,
    query_mi,
    query_raw,
)
from mq.utils import format_timestamp_headers

log = logging.getLogger(__name__)

RADON_SUB_MODULES = ("raw", "mi", "hal", "cc")


def report(args: Namespace) -> None:
    try:
        project = Project.get(path_input=args.project)
    except Project.DoesNotExist:
        log.error(f"Sorry, we didn't find any data yet for project: {args.project}")
        return None

    if args.sub_module:
        if not (run := Run.get_most_recent(project, MODULE, args.sub_module)):
            log.info(f"Sorry, we haven't performed a {args.sub_module} measurement yet for this project.")
        _dispatch_level_submodule(args, args.sub_module, run=run, project=project)
    else:
        for sub_module in RADON_SUB_MODULES:
            # Get most recent Run for simple "current-state" reporting..
            if not (run := Run.get_most_recent(project, MODULE, sub_module)):
                log.info(f"Sorry, we haven't performed a {sub_module} measurement yet for this project.")
                continue
            _dispatch_level_submodule(args, sub_module, run=run, project=project)


def _dispatch_level_submodule(args: Namespace, sub_module: str, run: Run = None, project: Project = None) -> None:
    """Dispatch to the report method using the report level and sub_module requested."""
    current_module = sys.modules[__name__]
    match args.level.lower():
        case "0":
            if method := getattr(current_module, f"_summary_{sub_module}"):
                method(args, run=run)
        case "1":
            if method := getattr(current_module, f"_detail_{sub_module}"):
                method(args, run=run)
        case "2":
            if method := getattr(current_module, f"_full_{sub_module}"):
                method(args, run=run)
        case "h":
            if method := getattr(current_module, f"_history_{sub_module}"):
                method(args, project=project)
        case _:
            log.warning(f"Sorry, invalid report level: '{args.level}', run mq report --help for valid options.")


################################################################################################
# Summary methods
################################################################################################
def _summary_raw(args: Namespace, run: Run) -> None:
    table = cli_table(title=f"RADON-RAW @ {run.timestamp_display}")
    # fmt: off
    table.add_column("LOC"             , justify="right")
    table.add_column("LLOC"            , justify="right")
    table.add_column("SLOC"            , justify="right")
    table.add_column("Comments"        , justify="right")
    table.add_column("Multi"           , justify="right")
    table.add_column("Blank"           , justify="right")
    table.add_column("Single Comments" , justify="right")
    # fmt: on
    for row in query_raw(args, "0", run):
        table.add_row(
            f"{row.loc:,}",
            f"{row.lloc:,}",
            f"{row.sloc:,}",
            f"{row.comments:,}",
            f"{row.multi:,}",
            f"{row.blank:,}",
            f"{row.single_comments:,}",
        )
    cli_console.print(table)


def _summary_hal(args: Namespace, run: Run) -> None:
    rows = query_hal(args, "0", run)
    # Calculate mean metric values
    means = {}
    for attr in RadonHal.attributes():
        values = [getattr(row, attr) for row in rows]
        means[attr] = sum(values) / len(values) if values else None

    table = cli_table(title=f"RADON-HAL @ {run.timestamp_display}", show_footer=True)
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
    cli_console.print(table)


def _summary_mi(args: Namespace, run: Run) -> None:
    row = query_mi(args, "0", run)
    table = cli_table(title=f"RADON-MI @ {run.timestamp_display}", show_header=False)
    table.add_column("_", style="bold magenta")
    table.add_column("_", style="bold magenta")
    table.add_row(
        "Composite Maintainability Score",
        f"{row.mi_mean:.2f}",
    )
    cli_console.print(table)


def _summary_cc(args: Namespace, run: Run) -> None:
    rows = query_cc(args, "0", run)
    table = cli_table(title=f"RADON-CC @ {run.timestamp_display}")
    table.add_column("Entity Type")
    table.add_column("Count", justify="center")
    for row in rows:
        table.add_row(row.entity_type, str(row.count))
    cli_console.print(table)


################################################################################################
# Detail methods
################################################################################################
def _detail_raw(args: Namespace, run: Run) -> None:
    rows, totals = query_raw(args, "1", run)

    table = cli_table(title=f"RADON-RAW @ {run.timestamp_display}")
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
    cli_console.print(table)


def _detail_hal(args: Namespace, run: Run) -> None:
    rows, means = query_hal(args, "1", run)

    table = cli_table(title=f"RADON-HAL @ {run.timestamp_display}", show_footer=True)
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
    cli_console.print(table)


def _detail_mi(args: Namespace, run: Run) -> None:
    rows, mean_mi_mean, mean_mi_mean_footer, show_footer = query_mi(args, "1", run)

    table = cli_table(title=f"RADON-MI @ {run.timestamp_display}", show_footer=show_footer)
    table.add_column("Directory", justify="left", footer="Composite Maintainability")
    table.add_column("Maintainability Index", justify="right", footer=mean_mi_mean_footer)
    for row in rows:
        table.add_row(
            row.dir,
            f"{row.mi_mean:.2f}",
        )
    cli_console.print(table)


def _detail_cc(args: Namespace, run: Run) -> None:
    rows = query_cc(args, "1", run)
    table = cli_table(title=f"RADON-CC @ {run.timestamp_display}")
    table.add_column("Directory", justify="left")
    table.add_column("Entity Type", justify="left")
    table.add_column("Count", justify="center")
    for row in rows:
        table.add_row(
            row.dir,
            row.entity_type,
            str(row.count),
        )
    cli_console.print(table)


################################################################################################
# 2 methods
################################################################################################
def _full_raw(args: Namespace, run: Run) -> None:
    rows = query_raw(args, "2", run)
    # Calculate grand totals
    totals = defaultdict(int)
    for row in rows:
        for attr in ("loc", "lloc", "sloc", "comments", "multi", "blank", "single_comments"):
            totals[attr] += getattr(row, attr)

    table = cli_table(title=f"RADON-RAW @ {run.timestamp_display}", show_footer=True)
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
    cli_console.print(table)


def _full_hal(args: Namespace, run: Run) -> None:
    rows, means = query_hal(args, "2", run)

    table = cli_table(title=f"RADON-HAL @ {run.timestamp_display}", show_footer=True)
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
    cli_console.print(table)


def _full_mi(args: Namespace, run: Run) -> None:
    rows, avg_footer, show_footer = query_mi(args, "2", run)

    table = cli_table(title=f"RADON-MI @ {run.timestamp_display}", show_footer=show_footer)
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
    cli_console.print(table)


def _full_cc(args: Namespace, run: Run) -> None:
    rows = query_cc(args, "2", run)
    table = cli_table(title=f"RADON-CC @ {run.timestamp_display}")
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
    cli_console.print(table)


################################################################################################
# History methods
################################################################################################
def _history_raw(args: Namespace, project: Project) -> None:
    timestamps, transposed, grand_totals, rocs, roc_gt = query_raw(args, "history", project=project)
    timestamps_formatted = format_timestamp_headers(timestamps)
    table = cli_table(title="RADON-RAW Results Over Time", show_footer=True)
    table.add_column("Metric", justify="left", footer="-")
    for timestamp in sorted(timestamps):
        table.add_column(timestamps_formatted[timestamp], justify="right", footer=f"{grand_totals[timestamp]:,d}")
    table.add_column("Delta", footer=f"{roc_gt:.2f}%")

    for metric, dt_rows in transposed.items():
        row = [metric]
        for timestamp in sorted(timestamps):
            row.append(f"{dt_rows[timestamp]:,d}")
        row.append(f"{rocs[metric]:.2f}%")
        table.add_row(*row)

    cli_console.print(table)


def _history_mi(args: Namespace, project: Project) -> None:
    timestamps, transposed, roc = query_mi(args, "history", project=project)
    timestamps_formatted = format_timestamp_headers(timestamps)
    table = cli_table(title="RADON-MI Results Over Time")
    table.add_column("Metric")
    for timestamp in sorted(timestamps):
        table.add_column(timestamps_formatted[timestamp], justify="right")
    table.add_column("Delta", justify="right")

    for metric, dt_rows in transposed.items():
        row = ["Maintainability Index"]
        for timestamp in sorted(timestamps):
            row.append(f"{dt_rows[timestamp]:.2f}")

        if roc > 0.01:
            color = COLORS["positive"]
        elif roc < -0.01:
            color = COLORS["negative"]
        else:
            color = COLORS["neutral"]

        row.append(f"[{color}][bold]{roc:+.2f}%[/bold][/{color}]")

        table.add_row(*row)
    cli_console.print(table)


def _history_hal(args: Namespace, project: Project) -> None: ...


def _history_cc(args: Namespace, project: Project) -> None: ...
