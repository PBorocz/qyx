"""..."""

import logging
from argparse import Namespace

from mq.cli import cli_console, cli_table
from mq.tools.base import Project, Scan
from mq.tools.radon.models import query_raw

log = logging.getLogger(__name__)


def raw_1(args: Namespace, project: Project = None, scan: Scan = None) -> None:
    rows, totals = query_raw(args, "1", scan)

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
