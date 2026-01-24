"""..."""

import logging
from argparse import Namespace

from mq.cli import cli_console, cli_table
from mq.tools.base import Project, Scan
from mq.tools.radon.models import query_hal


log = logging.getLogger(__name__)


def hal_d(args: Namespace, project: Project = None, scan: Scan = None) -> None:
    row = query_hal(args, "d", project=project, scan=scan)
    table = cli_table(title=f"RADON-HAL @ {scan.as_of_display()}")
    # fmt: off
    table.add_column("Metric" , justify="left")
    table.add_column("Value"  , justify="right")
    table.add_column("Grade"  , justify="center")
    table.add_row("Mean Bugs per kLOC"  , f"{row.bugs_d.score:.2f}"      , row.bugs_d.grade)
    table.add_row("Mean Difficulty"     , f"{row.difficulty_d.score:.2f}", row.difficulty_d.grade)
    table.add_row("Mean Effort per LOC" , f"{row.effort_d.score:.2f}"    , row.effort_d.grade)
    table.add_row("Composite Score"     , f"{row.composite_d.score:.2f}" , row.composite_d.grade)
    # fmt: on
    cli_console.print(table)
