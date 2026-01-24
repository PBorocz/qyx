"""..."""

import logging
from argparse import Namespace

from mq.cli import cli_console, cli_table
from mq.tools.base import Project, Scan
from mq.tools.radon.models import query_raw

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
    row = query_raw(args, "0", scan)
    table.add_row(
        f"{row.sloc:,} ({row.sloc_p:.1f}%)",
        f"{row.comments:,} ({row.comments_p:.1f}%)",
        f"{row.multi:,} ({row.multi_p:.1f}%)",
        f"{row.blank:,} ({row.blank_p:.1f}%)",
        f"{row.loc:,}",
    )
    cli_console.print(table)
