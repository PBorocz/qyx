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
    method_name = f"_{sub_module}_{args.level.lower()}"
    if method := getattr(current_module, method_name):
        method(args, run=run, project=project)
    else:
        log.warning(f"Sorry, invalid report level: '{args.level}', run mq report --help for valid options.")


################################################################################################
# RAW
################################################################################################
def _raw_0(args: Namespace, run: Run = None, project: Project = None) -> None:
    table = cli_table(title=f"RADON-RAW @ {run.timestamp_display}")
    # fmt: off
    table.add_column("LLOC"            , justify="right")
    table.add_column("SLOC"            , justify="right")
    table.add_column("Comments"        , justify="right")
    table.add_column("Multi"           , justify="right")
    table.add_column("Blank"           , justify="right")
    table.add_column("Single Comments" , justify="right")
    table.add_column("Total"           , justify="right")
    # fmt: on
    for row in query_raw(args, "0", run):
        table.add_row(
            f"{row.lloc:,}",
            f"{row.sloc:,}",
            f"{row.comments:,}",
            f"{row.multi:,}",
            f"{row.blank:,}",
            f"{row.single_comments:,}",
            f"{row.loc:,}",
        )
    cli_console.print(table)


def _raw_1(args: Namespace, run: Run = None, project: Project = None) -> None:
    rows, totals = query_raw(args, "1", run)

    table = cli_table(title=f"RADON-RAW @ {run.timestamp_display}", show_footer=True)
    # fmt: off
    table.add_column("Directory"       , justify="left")
    table.add_column("LLOC"            , justify="right", footer=f"{totals['lloc'            ]:,}")
    table.add_column("SLOC"            , justify="right", footer=f"{totals['sloc'            ]:,}")
    table.add_column("Comments"        , justify="right", footer=f"{totals['comments'        ]:,}")
    table.add_column("Multi"           , justify="right", footer=f"{totals['multi'           ]:,}")
    table.add_column("Blank"           , justify="right", footer=f"{totals['blank'           ]:,}")
    table.add_column("Single Comments" , justify="right", footer=f"{totals['single_comments' ]:,}")
    table.add_column("Total"           , justify="right", footer=f"{totals['loc'             ]:,}")
    # fmt: on
    for row in rows:
        table.add_row(
            row.dir,
            f"{row.lloc:,}",
            f"{row.sloc:,}",
            f"{row.comments:,}",
            f"{row.multi:,}",
            f"{row.blank:,}",
            f"{row.single_comments:,}",
            f"{row.loc:,}",
        )
    cli_console.print(table)


def _raw_2(args: Namespace, run: Run = None, project: Project = None) -> None:
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
    table.add_column("LLOC"            , justify="right", footer=f"{totals['lloc'            ]:,}")
    table.add_column("SLOC"            , justify="right", footer=f"{totals['sloc'            ]:,}")
    table.add_column("Comments"        , justify="right", footer=f"{totals['comments'        ]:,}")
    table.add_column("Multi"           , justify="right", footer=f"{totals['multi'           ]:,}")
    table.add_column("Blank"           , justify="right", footer=f"{totals['blank'           ]:,}")
    table.add_column("Single Comments" , justify="right", footer=f"{totals['single_comments' ]:,}")
    table.add_column("Total"           , justify="right", footer=f"{totals['loc'             ]:,}")
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


def _raw_h(args: Namespace, run: Run = None, project: Project = None) -> None:
    timestamps, transposed, rocs, roc_gt = query_raw(args, "h", project=project)
    timestamps_formatted = format_timestamp_headers(timestamps)
    table = cli_table(title="RADON-RAW Results Over Time", show_footer=True)
    table.add_column("Metric", justify="left", footer="-")
    for timestamp in sorted(timestamps):
        table.add_column(timestamps_formatted[timestamp], justify="right", footer=f"{transposed['loc'][timestamp]:,d}")
    table.add_column("Delta", footer=f"{roc_gt:.2f}%")

    for metric, dt_rows in transposed.items():
        if metric == "loc":  # We already picked this up above!
            continue
        row = [metric]
        for timestamp in sorted(timestamps):
            row.append(f"{dt_rows[timestamp]:,d}")

        roc = rocs[metric]
        if -0.01 < roc < 0.01:
            t_value = ""
        else:
            t_value = f"{roc:+.2f}%"

        row.append(t_value)
        table.add_row(*row)

    cli_console.print(table)


################################################################################################
# MI
################################################################################################
def _mi_0(args: Namespace, run: Run = None, project: Project = None) -> None:
    row = query_mi(args, "0", run)
    table = cli_table(title=f"RADON-MI @ {run.timestamp_display}", show_header=False)
    table.add_column("_", style="bold magenta")
    table.add_column("_", style="bold magenta")
    table.add_row(
        "Composite Maintainability Score",
        f"{row.mi_mean:.2f}",
    )
    cli_console.print(table)


def _mi_1(args: Namespace, run: Run = None, project: Project = None) -> None:
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


def _mi_2(args: Namespace, run: Run = None, project: Project = None) -> None:
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


def _mi_h(args: Namespace, run: Run = None, project: Project = None) -> None:
    timestamps, transposed, roc = query_mi(args, "h", project=project)
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


################################################################################################
# CC
################################################################################################
def _cc_0(args: Namespace, run: Run = None, project: Project = None) -> None:
    rows = query_cc(args, "0", run)
    table = cli_table(title=f"RADON-CC @ {run.timestamp_display}")
    table.add_column("Entity Type")
    table.add_column("Complexity", justify="right")
    table.add_column("Rank", justify="center")
    plurals = dict(Function="Functions", Method="Methods", Class="Classes")
    for row in rows:
        table.add_row(
            plurals[row.entity_type],
            f"{row.mean_complexity:.2f}",
            row.get_rank(row.mean_complexity),
        )
    cli_console.print(table)


def _cc_1(args: Namespace, run: Run = None, project: Project = None) -> None:
    rows = query_cc(args, "1", run)
    table = cli_table(title=f"RADON-CC @ {run.timestamp_display}")
    table.add_column("Directory", justify="left")
    table.add_column("Entity Type", justify="left")
    table.add_column("Complexity", justify="right")
    table.add_column("Rank", justify="center")
    plurals = dict(Function="Functions", Method="Methods", Class="Classes")
    for row in rows:
        table.add_row(
            row.dir,
            plurals[row.entity_type],
            f"{row.mean_complexity:.2f}",
            row.get_rank(row.mean_complexity),
        )
    cli_console.print(table)


def _cc_2(args: Namespace, run: Run = None, project: Project = None) -> None:
    rows = query_cc(args, "2", run)
    table = cli_table(title=f"RADON-CC @ {run.timestamp_display}")
    table.add_column("File", justify="left")
    table.add_column("Entity Type", justify="left")
    table.add_column("Complexity", justify="right")
    table.add_column("Rank", justify="center")
    plurals = dict(Function="Functions", Method="Methods", Class="Classes")
    for row in rows:
        table.add_row(
            f"{row.dir}/{row.filename}",
            plurals[row.entity_type],
            f"{row.mean_complexity:.2f}",
            row.get_rank(row.mean_complexity),
        )
    cli_console.print(table)


def _cc_3(args: Namespace, run: Run = None, project: Project = None) -> None:
    rows = query_cc(args, "3", run)
    table = cli_table(title=f"RADON-CC @ {run.timestamp_display}")
    table.add_column("File", justify="left")
    table.add_column("Entity Name", justify="left")
    table.add_column("Entity Type", justify="left")
    table.add_column("Complexity", justify="right")
    table.add_column("Rank", justify="center")
    for row in rows:
        table.add_row(
            f"{row.dir}/{row.filename}",
            row.entity_name,
            row.entity_type,
            f"{row.complexity:.2f}",
            row.rank,
        )
    cli_console.print(table)


def _cc_h(args: Namespace, run: Run = None, project: Project = None) -> None:
    timestamps, transposed, roc = query_cc(args, "h", project=project)
    timestamps_formatted = format_timestamp_headers(timestamps)
    table = cli_table(title="RADON-CC Results Over Time")
    table.add_column("Complexity", justify="left")
    for timestamp in sorted(timestamps):
        table.add_column(timestamps_formatted[timestamp], justify="right")
    table.add_column("Delta", footer=f"{roc:.2f}%")

    t_row = ["Complexity"]
    for timestamp in sorted(timestamps):
        t_row.append(f"{transposed['complexity'][timestamp]:.2f}")

    t_value = ""
    if roc > 0.01:
        color = COLORS["negative"]
        t_value = f"[{color}][bold]{roc:+.2f}%[/bold][/{color}]"

    elif roc < -0.01:
        color = COLORS["positive"]
        t_value = f"[{color}][bold]{roc:+.2f}%[/bold][/{color}]"

    t_row.append(t_value)
    table.add_row(*t_row)

    cli_console.print(table)


################################################################################################
# HAL
################################################################################################
def _hal_0(args: Namespace, run: Run = None, project: Project = None) -> None:
    row = query_hal(args, "0", run)
    table = cli_table(title=f"RADON-HAL @ {run.timestamp_display}")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    for display, attr, _ in RadonHal.attrs():
        table.add_row(display, f"{getattr(row, attr):.2f}")
    cli_console.print(table)


def _hal_1(args: Namespace, run: Run = None, project: Project = None) -> None:
    rows, mean_means = query_hal(args, "1", run)
    # Calculate mean metric values

    table = cli_table(title=f"RADON-HAL @ {run.timestamp_display}", show_footer=True)
    table.add_column("Directory", justify="left", footer="Mean")
    for display, attr, _ in RadonHal.attrs():
        table.add_column(display, justify="right", footer=f"{mean_means[attr]:.2f}")
    for row in rows:
        t_row = [row.dir]
        for _, attr, _ in RadonHal.attrs():
            t_row.append(f"{getattr(row, attr):.2f}")
        table.add_row(*t_row)
    cli_console.print(table)


def _hal_2(args: Namespace, run: Run = None, project: Project = None) -> None:
    rows, means = query_hal(args, "2", run)

    table = cli_table(title=f"RADON-HAL @ {run.timestamp_display}", show_footer=True)
    table.add_column("File", justify="left", footer="Mean")
    for display, attr, _ in RadonHal.attrs():
        table.add_column(display, justify="right", footer=f"{means[attr]:.2f}")
    for row in rows:
        t_row = [f"{row.dir}/{row.filename}"]
        for _, attr, fmt in RadonHal.attrs():
            if fmt == "float":
                value = f"{getattr(row, attr):.2f}"
            elif fmt == "int":
                value = f"{getattr(row, attr):,d}"
            t_row.append(value)
        table.add_row(*t_row)
    cli_console.print(table)


def _hal_3(args: Namespace, run: Run = None, project: Project = None) -> None:
    rows, means = query_hal(args, "3", run)

    table = cli_table(title=f"RADON-HAL @ {run.timestamp_display}", show_footer=True)
    table.add_column("File", justify="left", footer="Mean")
    table.add_column("Name", justify="left")
    for display, attr, _ in RadonHal.attrs():
        table.add_column(display, justify="right", footer=f"{means[attr]:.2f}")
    for row in rows:
        t_row = [f"{row.dir}/{row.filename}", row.name]
        for _, attr, fmt in RadonHal.attrs():
            if fmt == "float":
                value = f"{getattr(row, attr):.2f}"
            elif fmt == "int":
                value = f"{getattr(row, attr):,d}"
            t_row.append(value)
        table.add_row(*t_row)
    cli_console.print(table)


def _hal_h(args: Namespace, run: Run = None, project: Project = None) -> None:
    timestamps, transposed, grand_totals, rocs, roc_gt = query_hal(args, "h", project=project)
    timestamps_formatted = format_timestamp_headers(timestamps)
    table = cli_table(title="RADON-HAL Results Over Time", show_footer=True)
    table.add_column("Metric", justify="left", footer="-")
    for timestamp in sorted(timestamps):
        table.add_column(timestamps_formatted[timestamp], justify="right", footer=f"{grand_totals[timestamp]:.2f}")
    table.add_column("Delta", footer=f"{roc_gt:.2f}%")

    for attr, dt_rows in transposed.items():
        t_row = [attr]
        for timestamp in sorted(timestamps):
            t_row.append(f"{dt_rows[timestamp]:.2f}")

        roc = rocs[attr]
        t_value = ""
        if roc > 0.01:
            color = COLORS["positive"]
            t_value = f"[{color}][bold]{roc:+.2f}%[/bold][/{color}]"

        elif roc < -0.01:
            color = COLORS["negative"]
            t_value = f"[{color}][bold]{roc:+.2f}%[/bold][/{color}]"

        t_row.append(t_value)
        table.add_row(*t_row)

    cli_console.print(table)
