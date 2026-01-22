"""..."""

import logging
from argparse import Namespace

from peewee import fn

from mq.cli import cli_console
from mq.cli.admin import do_it
from mq.tools.base import Project, Request, Scan

log = logging.getLogger(__name__)


def trim(args: Namespace) -> None:
    """Clear/delete/*TRIM* all data associated with "old" scan, ie, lose history but keep most recent!"""
    # TODO: Implement ability to trim by Project (we already handle module below)
    raise NotImplementedError("!")

    if do_it(args, "This will delete 'older' data! (leaving the most recent Scan for each module & project)"):
        count = _trim(args)
        if count:
            msg = f"[green]✓ {count:,} old scans cleared successfully.[/green]"
        else:
            msg = "[green]✓ No old scans found.[/green]"

    else:
        msg = "[blue]Ok, nothing done.[/blue]"
    cli_console.print(msg)


def _trim(args: Namespace) -> int:
    """Trim scans that are NOT the most recent for each project, module and sub-module."""
    # Get the *most recent* scan for each combination of project, module and sub-module.
    scans_to_keep = (
        Scan.select(
            Scan.id,
            Scan.request,
            Project.name.alias("project_name"),
            Scan.module,
            Scan.sub_module,
            fn.MAX(Request.id).alias("max_id"),
        )
        .join(Request)
        .join(Project)
        .group_by(Project, Scan.module, Scan.sub_module)
        .objects()
    )

    log.debug("The following scans are the most current:")
    for scan in scans_to_keep:
        log.debug(f"{scan.id=} {scan.project_name} {scan.request.id=} {scan.module=} {scan.sub_module=}")

    # Delete scans that *ARE NOT* the most recent:
    count = 0
    for scan in Scan.select().join(Request):
        if scan.id not in [scan.id for scan in scans_to_keep]:
            if args.module and args.module != scan.module:
                continue
            # Scan.delete().where(Scan.id == scan.id).execute()
            log.debug(f"Deleted Scan {scan.id} as of {scan.timestamp}")
            count += 1
    return count
