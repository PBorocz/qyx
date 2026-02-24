"""..."""

import logging
from argparse import Namespace
from types import SimpleNamespace as Sns

from qyx.cli import cli_console, cli_table
from qyx.constants import ReportLevel as Rl
from qyx.tools.base import Project, Scan, ToolType
from qyx.tools.ruff.models import query_0, query_1, query_2, query_h
from qyx.utils import format_timestamp_headers

log = logging.getLogger(__name__)


def render(args: Namespace, project: Project, o_tool: ToolType, analysis: str) -> None:
    # Get most recent Scan for simple "current-state" reporting.
    # Note: We safely can disregard whether or not the Scan was based on
    # git or directly from a directory as we're searching based on "as of",
    # thus, the most recent scan could be from either source!
    if not (scan := Scan.get_most_recent(project, "ruff", "ruff")):
        log.error("Sorry, we haven't performed a 'ruff' scan yet for this project.")
        return None

    log.debug(f"{scan=}")
    match args.level.lower():
        case Rl.SUMMARY:
            ruff_0(args, project, scan)
        case Rl.DIRECTORY:
            ruff_1(args, project, scan)
        case Rl.FILE:
            ruff_2(args, scan)
        case Rl.HISTORY:
            ruff_h(args, project)
        case Rl.ALL:
            ruff_0(args, project, scan)
            ruff_1(args, project, scan)
            ruff_2(args, scan)
            ruff_h(args, project)
        case _:
            log.warning(f"Sorry, invalid report level: '{args.level}', run 'qyx report --help' for valid options.")


def ruff_0(args: Namespace, project: Project, scan: Scan) -> None:
    result: Sns = query_0(args, project, scan)
    table = cli_table(title=f"RUFF @ {scan.as_of_display()}")
    # table.add_column("_", style="bold magenta")
    # table.add_column("_", style="bold magenta")
    # table.add_row("Issues", f"{row.count:,d}")
    # cli_console.print(table)

    table.add_column("Metric", justify="left")
    table.add_column("Value", justify="right")
    table.add_column("Grade", justify="center")

    table.add_row("Raw Ruff Issues", f"{result.count:,d}", "-")

    if result.violations_per_kloc:
        table.add_row(
            "Raw Ruff Issues per kLOC",
            f"{result.violations_per_kloc.score:.0f}",
            f"{result.violations_per_kloc.grade}",
        )
    if result.weighted_violations_per_kloc:
        table.add_row(
            "Weighted Ruff Issues per kLOC",
            f"{result.weighted_violations_per_kloc.score:.0f}",
            f"{result.weighted_violations_per_kloc.grade}",
        )
    cli_console.print(table)


def ruff_1(args: Namespace, project: Project, scan: Scan) -> None:
    result: Sns = query_1(scan)
    table = cli_table(title=f"RUFF @ {scan.as_of_display()}")
    table.add_column("Rule", footer="TOTAL")
    table.add_column("Count", justify="right")
    table.add_column("Message")
    for row in result.rows:
        table.add_row(row.rule_code, f"{row.count:,d}", row.rule_name.title())
    cli_console.print(table)


def ruff_2(args: Namespace, scan: Scan) -> None:
    result: Sns = query_2(scan)
    table = cli_table(title=f"RUFF @ {scan.as_of_display()}")
    table.add_column("Rule")
    table.add_column("File [line]")
    table.add_column("Message")
    for row in result.rows:
        table.add_row(row.rule_code, f"{row.directory}/{row.filename} [{row.line}] ", row.message)
    cli_console.print(table)


# History at the Rl.SUMMARY level...
def ruff_h(args: Namespace, project: Project) -> None:
    """Report on the history of scans "across"."""
    timestamps, _, rows, roc = query_h(project, last=5)
    timestamps_formatted = format_timestamp_headers(timestamps)

    ################################################################################################
    # Render the table
    ################################################################################################
    table = cli_table(title="RUFF Results Over Time")
    table.add_column("-")
    for timestamp in sorted(timestamps):
        table.add_column(
            timestamps_formatted[timestamp],
            justify="right",
        )
    table.add_column("Delta")

    row = ["Issues"]
    for timestamp in sorted(timestamps):
        row.append(str(rows[timestamp]))

    colors = args.config.get("renderers.cli.colors")
    color = colors["neutral"]
    if roc:
        if roc > 0.01:
            color = colors["positive"]
        elif roc < -0.01:
            color = colors["negative"]
        row.append(f"[{color}][bold]{roc:+.2f}%[/bold][/{color}]")

    table.add_row(*row)

    cli_console.print(table)
