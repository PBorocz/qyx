"""Database housekeeping method."""

import logging
from argparse import Namespace
from datetime import datetime, timedelta

from qyx.tools.base import ToolType, Project, Request, Scan
from qyx.utils import dt_to_display

log = logging.getLogger(__name__)


def clean(args: Namespace, vacuum: bool = True) -> None:
    """Clean out extraneous Scans that don't have data and Projects that don't have Scans."""
    _delete_superseded_requests(args)
    _delete_orphaned_scans(args)
    _delete_orphaned_requests(args)
    _delete_orphaned_projects(args)
    if vacuum:  # This is time-consuming, only perform on formal clean request!
        _vacuum(args)


def _vacuum(args: Namespace) -> None:
    """Reclaim space."""
    args._db.execute_sql("VACUUM")


def _delete_superseded_requests(args: Namespace) -> None:
    """Delete Requests that have been superceded by git revision requests.

    - For projects that have requests/scans based on git revision history,
      we don't need to keep requests that are older than the most recent revision.

    - However, for projects without git history, we KEEP all requests are the
      sole source of history (and thus, do nothing here).
    """
    for project in Project.select():
        # Does this project have a git-based request that we reuse to keep statistics?
        try:
            git_request = Request.select().where(Request.project == project, Request.is_git).get()
        except Request.DoesNotExist:
            continue  # Nope, we're done with the project

        # Yes, Find the most recent scan for the git request (if any!):
        latest_git_scan = Scan.select().where(Scan.request == git_request).order_by(Scan.as_of.desc()).first()
        if not latest_git_scan:
            continue

        # Delete the scans of NON-GIT based requests for the project that occurred BEFORE the cutoff time!
        # (keeping a small buffer in case of clock skew)
        cutoff = datetime.fromisoformat(latest_git_scan.as_of) - timedelta(minutes=2)
        num = 0
        for local_request in Request.select().where(Request.project == project, ~Request.is_git):
            num += Scan.delete().where(Scan.request == local_request, Scan.timestamp <= cutoff).execute()
        if num:
            msg = (
                f"{project.name}: Cleaned up {num} scans that have been "
                f"superseded by latest git-revision of {dt_to_display(latest_git_scan.as_of)}"
            )
        else:
            msg = (
                f"{project.name}: Nothing done, no scans have been "
                f"superseded by latest git-revision of {dt_to_display(latest_git_scan.as_of)}"
            )
        log.debug(msg)


def _delete_orphaned_scans(args: Namespace) -> None:
    """Delete orphaned Scan, ie. that don't have results associated with 'em."""

    def __clean_scans(o_tool: ToolType) -> None:
        # First, get all the scan's id's used by models storing data for this tool/module:
        model_scan_ids = set()
        for models in o_tool.models.values():
            for model in models:
                result_scan_ids = [row.scan_id for row in model.select(model.scan).distinct()]
                model_scan_ids.update(result_scan_ids)
                log.debug(f"-- Analysis: {model.__name__:16s} has {len(result_scan_ids):2d} scan(s)")

        log.debug(f"- {o_tool.name:6s} {len(model_scan_ids):4d} scan definitions")

        # Secondly, gather all the scan's currently stored for this tool
        scan_ids = {scan.id for scan in Scan.select().where(Scan.tool == o_tool.name)}
        log.debug(f"- {o_tool.name:6s} {len(scan_ids):4d} scan with results")

        # Find any "orphaned" ones by simple set subtract (!) and delete 'em.
        scan_ids_to_delete = scan_ids - model_scan_ids
        if scan_ids_to_delete:
            Scan.delete().where(Scan.id.in_(scan_ids_to_delete)).execute()
            log.debug(f"- Cleaned up {len(scan_ids_to_delete)} orphaned Scan(s)")

    for o_tool in args.tools.values():
        log.debug("#" * 40)
        log.debug(f"Cleanup {o_tool.name=}")
        if o_tool.results_required:
            __clean_scans(o_tool)
        else:
            log.debug("Nothing done (tool is allowed to have scans with no results)")


def _delete_orphaned_requests(args: Namespace) -> None:
    """Delete orphaned Requests, ie. that don't have scans associated with 'em."""
    num = Request.delete().where(Request.id.not_in(Scan.select(Scan.request).distinct())).execute()
    if num:
        log.debug(f"Cleaned up {num} orphaned Requests")
    else:
        log.debug("Nothing done, no orphaned Requests encountered")


def _delete_orphaned_projects(args: Namespace):
    """Delete orphaned Projects, ie. that don't have requests associated with 'em."""
    num = Project.delete().where(Project.id.not_in(Request.select(Request.project).distinct())).execute()
    if num:
        log.debug(f"Cleaned up {num} orphaned Projects")
    else:
        log.debug("Nothing done, no orphaned Projects encountered")
