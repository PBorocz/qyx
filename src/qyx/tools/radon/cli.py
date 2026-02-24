"""CLI rendering obo 'radon' tool."""

import logging
from argparse import Namespace
from collections import defaultdict
from typing import Callable

from qyx.cli import cli_console, cli_table
from qyx.constants import ReportLevel as Rl
from qyx.constants import ViewContext as Vc
from qyx.tools.base import Project, Scan, ToolType
from qyx.tools.radon import models as rm
from qyx.tools.radon.models import RadonHal
from qyx.utils import format_timestamp_headers

log = logging.getLogger(__name__)


def render(args: Namespace, project: Project, o_tool: ToolType, analysis: str) -> None:
    if not (scan := Scan.get_most_recent(project, "radon", analysis)):
        log.info(f"Sorry, we haven't performed a '{analysis}' measurement yet for this project.")
        return None

    if args.level != Rl.ALL:
        # We're only running a single report..
        method: Callable = globals().get(f"{analysis}_{args.level.lower()}")  # Lookup from below..
        if not method:
            log.error(f"Sorry, invalid report level: '{args.level}', run qyx report --help for valid options.")
            return
        method(args, project=project, scan=scan)
    else:
        for rl_ in Rl:
            method: Callable = globals().get(f"{analysis}_{rl_.value}")  # Lookup from below..
            if method:
                method(args, project=project, scan=scan)


################################################################################################
# View methods
################################################################################################
################################################################################
# CC
################################################################################
def cc_0(args: Namespace, project: Project, scan: Scan) -> None:
    rows = rm.query_cc_0(args, scan)
    table = cli_table(title=f"RADON-CC @ {scan.as_of_display()}")
    table.add_column("Entity Type")
    table.add_column("Complexity", justify="right")
    table.add_column("Grade", justify="center")
    for row in rows:
        table.add_row(
            row.entity_type,
            row.rank,
            f"{row.metric.score:.1f}",
            row.metric.grade,
        )
    cli_console.print(table)


def cc_1(args: Namespace, project: Project, scan: Scan) -> None:
    rows = rm.query_cc_1(args, scan)
    table = cli_table(title=f"RADON-CC @ {scan.as_of_display()}")
    table.add_column("Directory", justify="left")
    table.add_column("Entity Type", justify="left")
    table.add_column("Complexity", justify="right")
    table.add_column("Grade", justify="center")
    for row in rows:
        table.add_row(
            row.directory,
            row.entity_type,
            f"{row.complexity:.2f}",
            row.metric.grade,
        )
    cli_console.print(table)


def cc_2(args: Namespace, project: Project, scan: Scan) -> None:
    rows = rm.query_cc_2(args, scan)
    table = cli_table(title=f"RADON-CC @ {scan.as_of_display()}")
    table.add_column("File", justify="left")
    table.add_column("Entity Type", justify="left")
    table.add_column("Complexity", justify="right")
    table.add_column("Grade", justify="center")
    for row in rows:
        table.add_row(
            f"{row.directory}/{row.filename}",
            row.entity_type,
            f"{row.complexity:.2f}",
            row.metric.grade,
        )
    cli_console.print(table)


def cc_3(args: Namespace, project: Project, scan: Scan) -> None:
    rows = rm.query_cc_3(args, scan)
    table = cli_table(title=f"RADON-CC @ {scan.as_of_display()}")
    table.add_column("File", justify="left")
    table.add_column("Entity Name", justify="left")
    table.add_column("Entity Type", justify="left")
    table.add_column("Complexity", justify="right")
    table.add_column("Grade", justify="center")
    for row in rows:
        table.add_row(
            f"{row.directory}/{row.filename}",
            row.entity_name,
            row.entity_type,
            f"{row.complexity:.2f}",
            row.metric.grade,
        )
    cli_console.print(table)


def cc_h(args: Namespace, project: Project, scan: Scan) -> None:
    timestamps, _, transposed, roc = rm.query_cc_h(project, last=5)
    timestamps_formatted = format_timestamp_headers(timestamps)
    table = cli_table(title="RADON-CC Results Over Time")
    table.add_column("Complexity", justify="left")
    for timestamp in sorted(timestamps):
        table.add_column(timestamps_formatted[timestamp], justify="right")
    table.add_column("Delta")

    colors = args.config.get("renderers.cli.colors")
    for entity_type, values in transposed.items():
        t_row = [entity_type]
        for timestamp in sorted(timestamps):
            t_row.append(f"{values[timestamp]:.2f}")

        t_value = ""
        roc_ = roc.get(entity_type, 0)
        if roc_ > 0.01:
            color = colors["negative"]
            t_value = f"[{color}][bold]{roc_:+.2f}%[/bold][/{color}]"
        elif roc_ < -0.01:
            color = colors["positive"]
            t_value = f"[{color}][bold]{roc_:+.2f}%[/bold][/{color}]"
        else:
            t_value = ""

        t_row.append(t_value)

        table.add_row(*t_row)

    cli_console.print(table)


################################################################################
# HAL
################################################################################
def hal_0(args: Namespace, project: Project, scan: Scan) -> None:
    row = rm.query_hal_0(args, project, scan)
    table = cli_table(title=f"RADON-HAL @ {scan.as_of_display()}")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    table.add_column("Grade", justify="center")

    table.add_row("Composite Score", f"{row.composite_d.score:.1f}", row.composite_d.grade)
    table.add_row("Mean Bugs per kLOC", f"{row.bugs_d.score:.1f}", row.bugs_d.grade)
    table.add_row("Mean Effort per LOC", f"{row.effort_d.score:.1f}", row.effort_d.grade)
    table.add_row("Mean Difficulty", f"{row.difficulty_d.score:.1f}", row.difficulty_d.grade)

    for attr in RadonHal.attrs():
        table.add_row(attr.display, f"{getattr(row, attr.name):.1f}")
    cli_console.print(table)


# def hal_d(args: Namespace, project: Project, scan: Scan) -> None:
#     row = rm.query_hal_d(args, project, scan)
#     table = cli_table(title=f"RADON-HAL @ {scan.as_of_display()}")
#     # fmt: off
#     table.add_column("Metric" , justify="left")
#     table.add_column("Value"  , justify="right")
#     table.add_column("Grade"  , justify="center")
#     # fmt: on
#     cli_console.print(table)


def hal_1(args: Namespace, project: Project, scan: Scan) -> None:
    rows, mean_means = rm.query_hal_1(scan)
    table = cli_table(title=f"RADON-HAL @ {scan.as_of_display()}", show_footer=True)
    table.add_column("Directory", justify="left", footer="Mean")
    for attr in RadonHal.attrs():
        table.add_column(attr.display, justify="right", footer=f"{mean_means[attr.name]:.1f}")
    for row in rows:
        t_row = [row.directory]
        for attr in RadonHal.attrs():
            t_row.append(f"{getattr(row, attr.name):.1f}")
        table.add_row(*t_row)
    cli_console.print(table)


def hal_2(args: Namespace, project: Project, scan: Scan) -> None:
    rows, means = rm.query_hal_2(scan)

    table = cli_table(title=f"RADON-HAL @ {scan.as_of_display()}", show_footer=True)
    table.add_column("File", justify="left", footer="Mean")
    for attr in RadonHal.attrs():
        table.add_column(attr.display, justify="right", footer=f"{means[attr.name]:.1f}")
    for row in rows:
        t_row = [f"{row.directory}/{row.filename}"]
        for attr in RadonHal.attrs():
            if attr.type == "float":
                value = f"{getattr(row, attr.name):.1f}"
            elif attr.type == "int":
                value = f"{getattr(row, attr.name):,d}"
            t_row.append(value)
        table.add_row(*t_row)
    cli_console.print(table)


def hal_3(args: Namespace, project: Project, scan: Scan) -> None:
    rows, means = rm.query_hal_3(scan)

    table = cli_table(title=f"RADON-HAL @ {scan.as_of_display()}", show_footer=True)
    table.add_column("File", justify="left", footer="Mean")
    table.add_column("Name", justify="left")
    for attr in RadonHal.attrs():
        table.add_column(attr.display, justify="right", footer=f"{means[attr.name]:.1f}")
    for row in rows:
        t_row = [f"{row.directory}/{row.filename}", row.name]
        for attr in RadonHal.attrs():
            if attr.type == "float":
                value = f"{getattr(row, attr.name):.1f}"
            elif attr.type == "int":
                value = f"{getattr(row, attr.name):,d}"
            t_row.append(value)
        table.add_row(*t_row)
    cli_console.print(table)


def hal_h(args: Namespace, project: Project, scan: Scan) -> None:
    timestamps, _, transposed, rocs = rm.query_hal_h(project, last=5)
    timestamps_formatted = format_timestamp_headers(timestamps)
    table = cli_table(title="RADON-HAL Results Over Time")
    table.add_column("Metric", justify="left")
    for timestamp in sorted(timestamps):
        table.add_column(timestamps_formatted[timestamp], justify="right")
    table.add_column("Delta")

    colors = args.config.get("renderers.cli.colors")
    for attr, dt_rows in transposed.items():
        t_row = [attr]
        for timestamp in sorted(timestamps):
            t_row.append(f"{dt_rows[timestamp]:.1f}")

        if attr in rocs:
            roc = rocs[attr]
            t_value = ""
            if roc > 0.01:
                color = colors["positive"]
                t_value = f"[{color}][bold]{roc:+.1f}%[/bold][/{color}]"

            elif roc < -0.01:
                color = colors["negative"]
                t_value = f"[{color}][bold]{roc:+.1f}%[/bold][/{color}]"
        else:
            t_value = ""

        t_row.append(t_value)
        table.add_row(*t_row)

    cli_console.print(table)


################################################################################
# MI
################################################################################
def mi_0(args: Namespace, project: Project, scan: Scan) -> None:
    mi_metric = rm.query_mi_0(args, scan)
    table = cli_table(title=f"RADON-MI @ {scan.as_of_display()}", show_header=False, show_footer=False)
    table.add_column("", justify="left")
    table.add_column("", justify="left")
    table.add_column("", justify="left")
    table.add_row("Composite Maintainability Score (Weighted)", f"{mi_metric.score:.2f}", mi_metric.grade)
    cli_console.print(table)


def mi_1(args: Namespace, project: Project, scan: Scan) -> None:
    mi_metric, mi_by_directory = rm.query_mi_1(args, scan)
    show_footer = True if mi_metric else False

    table = cli_table(title=f"RADON-MI @ {scan.as_of_display()}", show_footer=show_footer)
    table.add_column("Directory", justify="left", footer="Composite Maintainability")
    table.add_column("Maintainability Index (Weighted)", justify="right", footer=f"{mi_metric.score:.2f}")
    for directory, mi_dir in mi_by_directory.items():
        table.add_row(
            directory,
            f"{mi_dir:.2f}",
        )
    cli_console.print(table)


def mi_2(args: Namespace, project: Project, scan: Scan) -> None:
    mi_metric, rows = rm.query_mi_2(args, scan)
    show_footer = True if mi_metric else False

    table = cli_table(title=f"RADON-MI @ {scan.as_of_display()}", show_footer=show_footer)
    table.add_column("Directory", justify="left", footer="Composite Maintainability")
    table.add_column("Filename", justify="left")
    table.add_column("Maintainability Index", justify="right", footer=f"{mi_metric.score:.2f}")
    table.add_column("Rank", justify="center")
    for row in rows:
        table.add_row(
            row.directory,
            row.filename,
            f"{row.mi:.2f}",
            row.rank,
        )
    cli_console.print(table)


def mi_h(args: Namespace, project: Project, scan: Scan) -> None:
    _, rows, roc = rm.query_mi_h(project, last=5)
    timestamps = list(rows.keys())
    timestamps_formatted = format_timestamp_headers(timestamps)

    table = cli_table(title="RADON-MI Results Over Time")
    table.add_column("Metric")
    for timestamp in sorted(timestamps):
        table.add_column(timestamps_formatted[timestamp], justify="right")
    table.add_column("Delta", justify="right")

    row = ["Maintainability Index"]
    for timestamp in sorted(timestamps):
        row.append(f"{rows[timestamp]:.2f}")

    colors = args.config.get("renderers.cli.colors")
    if roc > 0.01:
        color = colors["negative"]
    elif roc < -0.01:
        color = colors["positive"]
    else:
        color = colors["neutral"]

    row.append(f"[{color}][bold]{roc:+.2f}%[/bold][/{color}]")

    table.add_row(*row)

    cli_console.print(table)


################################################################################
# RAW
################################################################################
def raw_0(args: Namespace, project: Project, scan: Scan) -> None:
    table = cli_table(title=f"RADON-RAW @ {scan.as_of_display()}")
    # fmt: off
    table.add_column("SLOC"    , justify="right")
    table.add_column("Comment" , justify="right")
    table.add_column("Multi"   , justify="right")
    table.add_column("Blank"   , justify="right")
    table.add_column("Total"   , justify="right")
    # fmt: on
    row = rm.query_raw_0(scan)
    table.add_row(
        f"{row.sloc:,} ({row.sloc_p:.1f}%)",
        f"{row.comments:,} ({row.comments_p:.1f}%)",
        f"{row.multi:,} ({row.multi_p:.1f}%)",
        f"{row.blank:,} ({row.blank_p:.1f}%)",
        f"{row.loc:,}",
    )
    cli_console.print(table)


def raw_1(args: Namespace, project: Project, scan: Scan) -> None:
    rows, totals = rm.query_raw_1(scan)

    table = cli_table(title=f"RADON-RAW @ {scan.as_of_display()}", show_footer=True)
    # fmt: off
    table.add_column("Directory" , justify="left")
    table.add_column("SLOC"      , justify="right", footer=f"{totals['sloc'            ]:,}")
    table.add_column("Comment"   , justify="right", footer=f"{totals['comments'        ]:,}")
    table.add_column("Multi"     , justify="right", footer=f"{totals['multi'           ]:,}")
    table.add_column("Blank"     , justify="right", footer=f"{totals['blank'           ]:,}")
    table.add_column("Total"     , justify="right", footer=f"{totals['loc'             ]:,}")
    # fmt: on
    for row in rows:
        table.add_row(
            row.directory,
            f"{row.sloc:,}",
            f"{row.comments:,}",
            f"{row.multi:,}",
            f"{row.blank:,}",
            f"{row.loc:,}",
        )
    cli_console.print(table)


def raw_2(args: Namespace, project: Project, scan: Scan) -> None:
    rows = rm.query_raw_2(scan)
    # Calculate grand totals
    totals = defaultdict(int)
    for row in rows:
        for attr in ("loc", "sloc", "comments", "multi", "blank"):
            totals[attr] += getattr(row, attr)

    table = cli_table(title=f"RADON-RAW @ {scan.as_of_display()}", show_footer=True)
    # fmt: off
    table.add_column("Directory"       , justify="left")
    table.add_column("File"            , justify="left")
    table.add_column("SLOC"            , justify="right", footer=f"{totals['sloc'            ]:,}")
    table.add_column("Comments"        , justify="right", footer=f"{totals['comments'        ]:,}")
    table.add_column("Multi"           , justify="right", footer=f"{totals['multi'           ]:,}")
    table.add_column("Blank"           , justify="right", footer=f"{totals['blank'           ]:,}")
    table.add_column("Total"           , justify="right", footer=f"{totals['loc'             ]:,}")
    # fmt: on
    for row in rows:
        table.add_row(
            row.directory,
            row.filename,
            f"{row.loc:,}",
            f"{row.sloc:,}",
            f"{row.comments:,}",
            f"{row.multi:,}",
            f"{row.blank:,}",
        )
    cli_console.print(table)


def raw_h(args: Namespace, project: Project, scan: Scan) -> None:
    timestamps, _, transposed, rocs, roc_gt = rm.query_raw_h(project, last=5)
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

            t_value = ""
        if metric in rocs:
            roc = rocs[metric]
            if roc:
                if -0.01 < roc < 0.01:
                    t_value = ""
                else:
                    t_value = f"{roc:+.2f}%"

        row.append(t_value)
        table.add_row(*row)

    cli_console.print(table)
