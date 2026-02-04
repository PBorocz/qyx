"""..."""

import logging
from argparse import Namespace

from mq.tools.base import ToolType, Project, Request, Scan

log = logging.getLogger(__name__)


def clean(args: Namespace) -> None:
    """Clean out extraneous Scans that don't have data and Projects that don't have Scans."""
    _delete_extraneous_scans(args)
    _delete_extraneous_requests(args)
    _delete_extraneous_projects(args)


def _delete_extraneous_scans(args: Namespace) -> None:
    """Delete orphaned Scan, ie. that don't have results associated with 'em."""

    def __clean_scans(o_tool: ToolType) -> None:
        # First, get all the scan's id's used by models storing data for this tool/module:
        model_scan_ids = set()
        for models in o_tool.models.values():
            for model in models:
                result_scan_ids = [row.scan_id for row in model.select(model.scan).distinct()]
                model_scan_ids.update(result_scan_ids)
                log.debug(f"-- Analysis: {model.__name__:16s} has {len(result_scan_ids):2d} scan(s).")

        log.debug(f"- {o_tool.name:6s} {len(model_scan_ids):4d} scan definitions.")

        # Secondly, gather all the scan's currently stored for this tool
        scan_ids = {scan.id for scan in Scan.select().where(Scan.tool == o_tool.name)}
        log.debug(f"- {o_tool.name:6s} {len(scan_ids):4d} scan with results.")

        # Find any "extraneous" ones by simple set subtract (!) and delete 'em.
        scan_ids_to_delete = scan_ids - model_scan_ids
        if scan_ids_to_delete:
            Scan.delete().where(Scan.id.in_(scan_ids_to_delete)).execute()
            log.debug(f"- Cleaned up {len(scan_ids_to_delete)} Scan(s) that have *no* results associated with them.")

    for o_tool in args.tools.values():
        log.debug("#" * 40)
        log.debug(f"Cleanup {o_tool.name=}")
        if o_tool.results_required:
            __clean_scans(o_tool)
        else:
            log.debug("Nothing done, tool is allowed to have scans with no results.")


def _delete_extraneous_requests(args: Namespace) -> None:
    """Delete orphaned Requests, ie. that don't have scans associated with 'em."""
    num = Request.delete().where(Request.id.not_in(Scan.select(Scan.request).distinct())).execute()
    if num:
        log.debug(f"Cleaned up {num} Requests that had no Scans defined on their behalf.")
    else:
        log.debug("Nothing done, all Requests have Scans associated with them.")


def _delete_extraneous_projects(args: Namespace):
    """Delete orphaned Projects, ie. that don't have requests associated with 'em."""
    num = Project.delete().where(Project.id.not_in(Request.select(Request.project).distinct())).execute()
    if num:
        log.debug(f"Cleaned up {num} Projects that had no Requests defined on their behalf.")
    else:
        log.debug("Nothing done, all Projects have Requests associated with them.")
