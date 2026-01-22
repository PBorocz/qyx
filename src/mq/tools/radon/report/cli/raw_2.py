"""..."""

import logging
from collections import defaultdict

from mq.cli import cli_console, cli_table
from mq.tools.base import Project, Scan
from mq.tools.radon.models import query_raw

log = logging.getLogger(__name__)

RADON_SUB_TOOLS = ("raw", "mi", "hal", "cc")


def raw_2(project: Project = None, scan: Scan = None) -> None:
    rows = query_raw("2", scan)
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
