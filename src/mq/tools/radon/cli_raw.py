"""..."""

import logging
from argparse import Namespace
from collections import defaultdict

from mq.cli import cli_console, cli_table
from mq.constants import ReportLevel
from mq.tools.base import Project, Scan
from mq.tools.radon.models import query_raw

from mq.utils import format_timestamp_headers

log = logging.getLogger(__name__)


def raw_0(args: Namespace, project: Project = None, scan: Scan = None) -> None:
    table = cli_table(title=f"RADON-RAW @ {scan.as_of_display()}")
    # fmt: off
    table.add_column("SLOC"            , justify="right")
    table.add_column("Comments"        , justify="right")
    table.add_column("Multi"           , justify="right")
    table.add_column("Blank"           , justify="right")
    table.add_column("Total"           , justify="right")
    # fmt: on
    row = query_raw(args, ReportLevel.SUMMARY, scan)
    table.add_row(
        f"{row.sloc:,} ({row.sloc_p:.1f}%)",
        f"{row.comments:,} ({row.comments_p:.1f}%)",
        f"{row.multi:,} ({row.multi_p:.1f}%)",
        f"{row.blank:,} ({row.blank_p:.1f}%)",
        f"{row.loc:,}",
    )
    cli_console.print(table)


def raw_1(args: Namespace, project: Project = None, scan: Scan = None) -> None:
    rows, totals = query_raw(args, ReportLevel.DIRECTORY, scan)

    table = cli_table(title=f"RADON-RAW @ {scan.as_of_display()}", show_footer=True)
    # fmt: off
    table.add_column("Directory"       , justify="left")
    table.add_column("SLOC"            , justify="right", footer=f"{totals['sloc'            ]:,}")
    table.add_column("Comments"        , justify="right", footer=f"{totals['comments'        ]:,}")
    table.add_column("Multi"           , justify="right", footer=f"{totals['multi'           ]:,}")
    table.add_column("Blank"           , justify="right", footer=f"{totals['blank'           ]:,}")
    table.add_column("Total"           , justify="right", footer=f"{totals['loc'             ]:,}")
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


def raw_2(args: Namespace, project: Project = None, scan: Scan = None) -> None:
    rows = query_raw(args, ReportLevel.FILE, scan)
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


def raw_h(args: Namespace, project: Project = None, scan: Scan = None) -> None:
    timestamps, transposed, rocs, roc_gt = query_raw(args, ReportLevel.HISTORY, project=project, last=5)
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
