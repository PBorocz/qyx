"""CLI rendering obo 'radon' tool."""

import logging
from argparse import Namespace
from typing import Callable
from types import SimpleNamespace as Sns

from qyx.cli import cli_console, cli_table
from qyx.constants import ReportLevel
from qyx.tools._models_ import Project, Scan, ToolDimension, ToolType
from qyx.tools.radon import models as rm
from qyx.tools.radon.models import RadonHal
from qyx.utils import format_timestamp_headers

log = logging.getLogger(__name__)


def render(args: Namespace, project: Project, o_tool: ToolType, o_dimension: ToolDimension | str) -> bool:
    dimension = o_dimension.name if isinstance(o_dimension, ToolDimension) else o_dimension
    if not (scan := Scan.get_latest(project, "radon", dimension)):
        log.info(f"Sorry, we haven't performed a '{dimension}' measurement yet for this project.")
        return False

    if args.level != ReportLevel.ALL:
        # We're only running a single report..
        method: Callable = globals().get(f"{dimension}_{args.level.lower()}")  # Lookup from below..
        if not method:
            log.error(f"Sorry, invalid report level: '{args.level}', run qyx report --help for valid options.")
            return False
        method(args, project=project, scan=scan)
    else:
        for report_level in ReportLevel:
            method: Callable = globals().get(f"{dimension}_{report_level.value}")  # Lookup from below..
            if method:
                method(args, project=project, scan=scan)
    return True


################################################################################################
# View methods
################################################################################################
################################################################################
# CC
################################################################################
def cc_0(args: Namespace, project: Project, scan: Scan) -> None:
    result = rm.query_cc_0(args, scan)
    table = cli_table(title=f"RADON-CC @ {scan.as_of_display()}")
    table.add_column("Entity Type")
    table.add_column("Complexity", justify="right")
    table.add_column("Grade", justify="center")
    for row in result.rows:
        table.add_row(
            row.entity_type,
            row.rank,
            f"{row.metric.score:.1f}",
            row.metric.grade,
        )
    cli_console.print(table)


def cc_1(args: Namespace, project: Project, scan: Scan) -> None:
    result = rm.query_cc_1(args, scan)
    table = cli_table(title=f"RADON-CC @ {scan.as_of_display()}")
    table.add_column("Directory", justify="left")
    table.add_column("Entity Type", justify="left")
    table.add_column("Complexity", justify="right")
    table.add_column("Grade", justify="center")
    for row in result.rows:
        table.add_row(
            row.directory,
            row.entity_type,
            f"{row.complexity:.2f}",
            row.metric.grade,
        )
    cli_console.print(table)


def cc_2(args: Namespace, project: Project, scan: Scan) -> None:
    result = rm.query_cc_2(args, scan)
    table = cli_table(title=f"RADON-CC @ {scan.as_of_display()}")
    table.add_column("File", justify="left")
    table.add_column("Entity Type", justify="left")
    table.add_column("Complexity", justify="right")
    table.add_column("Grade", justify="center")
    for row in result.rows:
        table.add_row(
            f"{row.directory}/{row.filename}",
            row.entity_type,
            f"{row.complexity:.2f}",
            row.metric.grade,
        )
    cli_console.print(table)


def cc_3(args: Namespace, project: Project, scan: Scan) -> None:
    result = rm.query_cc_3(args, scan)
    table = cli_table(title=f"RADON-CC @ {scan.as_of_display()}")
    table.add_column("File", justify="left")
    table.add_column("Entity Name", justify="left")
    table.add_column("Entity Type", justify="left")
    table.add_column("Complexity", justify="right")
    table.add_column("Grade", justify="center")
    for row in result.rows:
        table.add_row(
            f"{row.directory}/{row.filename}",
            row.entity_name,
            row.entity_type,
            f"{row.complexity:.2f}",
            row.metric.grade,
        )
    cli_console.print(table)


def cc_h(args: Namespace, project: Project, scan: Scan) -> None:
    result = rm.query_cc_h(project, last=5)
    timestamps_formatted = format_timestamp_headers(result.timestamps)
    table = cli_table(title="RADON-CC Results Over Time")
    table.add_column("Complexity", justify="left")
    for timestamp in sorted(result.timestamps):
        table.add_column(timestamps_formatted[timestamp], justify="right")
    table.add_column("Delta")

    colors = args.config.get("renderers.cli.colors")
    for entity_type, values in result.transposed.items():
        t_row = [entity_type]
        for timestamp in sorted(result.timestamps):
            try:
                t_row.append(f"{values[timestamp]:.2f}")
            except TypeError:
                t_row.append("-")

        t_value = ""
        roc_ = result.rocs.get(entity_type, 0)
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
    result = rm.query_hal_0(args, scan)
    table = cli_table(title=f"RADON-HAL @ {scan.as_of_display()}")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    table.add_column("Grade", justify="center")

    table.add_row("Composite Score", f"{result.composite_d.score:.1f}", result.composite_d.grade)
    table.add_row("Mean Bugs per kLOC", f"{result.bugs_d.score:.1f}", result.bugs_d.grade)
    table.add_row("Mean Effort per LOC", f"{result.effort_d.score:.1f}", result.effort_d.grade)
    table.add_row("Mean Difficulty", f"{result.difficulty_d.score:.1f}", result.difficulty_d.grade)

    for attr in RadonHal.attrs():
        table.add_row(attr.display, f"{getattr(result, attr.name):.1f}")
    cli_console.print(table)


def hal_1(args: Namespace, project: Project, scan: Scan) -> None:
    result = rm.query_hal_1(scan)
    table = cli_table(title=f"RADON-HAL @ {scan.as_of_display()}", show_footer=True)
    table.add_column("Directory", justify="left", footer="Mean")
    for attr in RadonHal.attrs():
        table.add_column(attr.display, justify="right", footer=f"{result.mean_means[attr.name]:.1f}")
    for row in result.rows:
        t_row = [row.directory]
        for attr in RadonHal.attrs():
            t_row.append(f"{getattr(row, attr.name):.1f}")
        table.add_row(*t_row)
    cli_console.print(table)


def hal_2(args: Namespace, project: Project, scan: Scan) -> None:
    result = rm.query_hal_2(scan)

    table = cli_table(title=f"RADON-HAL @ {scan.as_of_display()}", show_footer=True)
    table.add_column("File", justify="left", footer="Mean")
    for attr in RadonHal.attrs():
        table.add_column(attr.display, justify="right", footer=f"{result.means[attr.name]:.1f}")
    for row in result.rows:
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
    result = rm.query_hal_3(scan)

    table = cli_table(title=f"RADON-HAL @ {scan.as_of_display()}", show_footer=True)
    table.add_column("File", justify="left", footer="Mean")
    table.add_column("Name", justify="left")
    for attr in RadonHal.attrs():
        table.add_column(attr.display, justify="right", footer=f"{result.means[attr.name]:.1f}")
    for row in result.rows:
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
    result = rm.query_hal_h(project, last=5)
    timestamps_formatted = format_timestamp_headers(result.timestamps)
    table = cli_table(title="RADON-HAL Results Over Time")
    table.add_column("Metric", justify="left")
    for timestamp in sorted(result.timestamps):
        table.add_column(timestamps_formatted[timestamp], justify="right")
    table.add_column("Delta")

    colors = args.config.get("renderers.cli.colors")
    for attr, dt_rows in result.transposed.items():
        t_row = [attr]
        for timestamp in sorted(result.timestamps):
            t_row.append(f"{dt_rows[timestamp]:.1f}")

        if attr in result.rocs:
            roc = result.rocs[attr]
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
    result = rm.query_mi_0(args, scan)
    table = cli_table(title=f"RADON-MI @ {scan.as_of_display()}", show_header=False, show_footer=False)
    table.add_column("", justify="left")
    table.add_column("", justify="left")
    table.add_column("", justify="left")
    table.add_row("Composite Maintainability Score (Weighted)", f"{result.mi_metric.score:.2f}", result.mi_metric.grade)
    cli_console.print(table)


def mi_1(args: Namespace, project: Project, scan: Scan) -> None:
    result = rm.query_mi_1(args, scan)
    show_footer = True if result.mi_metric else False

    table = cli_table(title=f"RADON-MI @ {scan.as_of_display()}", show_footer=show_footer)
    table.add_column("Directory", justify="left", footer="Composite Maintainability")
    table.add_column("Maintainability Index (Weighted)", justify="right", footer=f"{result.mi_metric.score:.2f}")
    table.add_column("Grade", justify="right", footer=f"{result.mi_metric.score:.2f}")
    for directory, metric in result.mi_by_directory.items():
        table.add_row(
            directory,
            f"{metric.score:.2f}",
            metric.grade,
        )
    cli_console.print(table)


def mi_2(args: Namespace, project: Project, scan: Scan) -> None:
    result = rm.query_mi_2(args, scan)
    show_footer = True if result.mi_metric else False

    table = cli_table(title=f"RADON-MI @ {scan.as_of_display()}", show_footer=show_footer)
    table.add_column("Directory", justify="left", footer="Composite Maintainability")
    table.add_column("Filename", justify="left")
    table.add_column("Maintainability Index", justify="right", footer=f"{result.mi_metric.score:.2f}")
    table.add_column("Grade", justify="center")
    for row in result.rows:
        table.add_row(
            row.directory,
            row.filename,
            f"{row.metric.score:.2f}",
            row.metric.grade,
        )
    cli_console.print(table)


def mi_h(args: Namespace, project: Project, scan: Scan) -> None:
    result = rm.query_mi_h(project, last=5)

    timestamps = list(result.rows.keys())
    timestamps_formatted = format_timestamp_headers(timestamps)

    table = cli_table(title="RADON-MI Results Over Time")
    table.add_column("Metric")
    for timestamp in sorted(timestamps):
        table.add_column(timestamps_formatted[timestamp], justify="right")
    table.add_column("Delta", justify="right")

    row = ["Maintainability Index"]
    for timestamp in sorted(timestamps):
        row.append(f"{result.rows[timestamp]:.2f}")

    colors = args.config.get("renderers.cli.colors")
    if result.roc > 0.01:
        color = colors["negative"]
    elif result.roc < -0.01:
        color = colors["positive"]
    else:
        color = colors["neutral"]

    row.append(f"[{color}][bold]{result.roc:+.2f}%[/bold][/{color}]")

    table.add_row(*row)

    cli_console.print(table)


################################################################################
# RAW
################################################################################
def raw_0(args: Namespace, project: Project, scan: Scan) -> None:
    result: Sns = rm.query_raw_0(args, scan)
    table = cli_table(title=f"RADON-RAW @ {scan.as_of_display()}")
    # fmt: off
    table.add_column("SLOC"    , justify="right")
    table.add_column("Comment" , justify="right")
    table.add_column("Multi"   , justify="right")
    table.add_column("Blank"   , justify="right")
    table.add_column("Total"   , justify="right")
    # fmt: on
    table.add_row(
        f"{result.sloc:,}",
        f"{result.comments:,}",
        f"{result.multi:,}",
        f"{result.blank:,}",
        f"{result.loc:,}",
    )
    table.add_row(
        f"{result.sloc_p:.1f}%",
        f"{result.comments_p:.1f}%",
        f"{result.multi_p:.1f}%",
        f"{result.blank_p:.1f}%",
    )
    cli_console.print(table)


def raw_1(args: Namespace, project: Project, scan: Scan) -> None:
    result: Sns = rm.query_raw_1(scan)
    table = cli_table(title=f"RADON-RAW @ {scan.as_of_display()}", show_footer=True)
    # fmt: off
    table.add_column("Directory" , justify="left")
    table.add_column("SLOC"      , justify="right", footer=f"{result.totals['sloc'     ]:,}")
    table.add_column("Comment"   , justify="right", footer=f"{result.totals['comments' ]:,}")
    table.add_column("Multi"     , justify="right", footer=f"{result.totals['multi'    ]:,}")
    table.add_column("Blank"     , justify="right", footer=f"{result.totals['blank'    ]:,}")
    table.add_column("Total"     , justify="right", footer=f"{result.totals['loc'      ]:,}")
    # fmt: on
    for row in result.rows:
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
    result = rm.query_raw_2(scan)
    table = cli_table(title=f"RADON-RAW @ {scan.as_of_display()}", show_footer=True)
    # fmt: off
    table.add_column("Directory"       , justify="left")
    table.add_column("File"            , justify="left")
    table.add_column("SLOC"            , justify="right", footer=f"{result.totals['sloc'     ]:,}")
    table.add_column("Comments"        , justify="right", footer=f"{result.totals['comments' ]:,}")
    table.add_column("Multi"           , justify="right", footer=f"{result.totals['multi'    ]:,}")
    table.add_column("Blank"           , justify="right", footer=f"{result.totals['blank'    ]:,}")
    table.add_column("Total"           , justify="right", footer=f"{result.totals['loc'      ]:,}")
    # fmt: on
    for row in result.rows:
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
    result = rm.query_raw_h(project, last=5)
    timestamps_formatted = format_timestamp_headers(result.timestamps)
    table = cli_table(title="RADON-RAW Results Over Time", show_footer=True)
    table.add_column("Metric", justify="left", footer="-")
    for timestamp in sorted(result.timestamps):
        table.add_column(
            timestamps_formatted[timestamp],
            justify="right",
            footer=f"{result.transposed['loc'][timestamp]:,d}",
        )
    table.add_column("Delta", footer=f"{result.roc_gt:.2f}%")

    for metric, dt_rows in result.transposed.items():
        if metric == "loc":  # We already picked this up above!
            continue
        row = [metric]
        for timestamp in sorted(result.timestamps):
            row.append(f"{dt_rows[timestamp]:,d}")

            t_value = ""
        if metric in result.rocs:
            roc = result.rocs[metric]
            if roc:
                if -0.01 < roc < 0.01:
                    t_value = ""
                else:
                    t_value = f"{roc:+.2f}%"

        row.append(t_value)
        table.add_row(*row)

    cli_console.print(table)
