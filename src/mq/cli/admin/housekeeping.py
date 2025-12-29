"""..."""

import logging
from argparse import Namespace

from mq.tools import AbstractModuleConfiguration
from mq.tools.base import Project, Request, Scan

log = logging.getLogger(__name__)


def housekeeping(args: Namespace) -> None:
    """Clean out extraneous Scans that don't have data and Projects that don't have Scans."""
    _delete_extraneous_scans(args)
    _delete_extraneous_requests(args)
    _delete_extraneous_projects(args)


def _delete_extraneous_scans(args: Namespace) -> None:
    """Delete orphaned Sequests, ie. that don't have results associated with 'em."""

    def __clean_scans(tool_name: str, tool_config: AbstractModuleConfiguration) -> None:
        # log.debug(f"Cleanup {tool_name=}")
        # First, get all the scan's id's used by models in this module:
        model_scan_ids = set()
        for model in tool_config.models:
            result_scan_ids = [row.scan_id for row in model.select(model.scan).distinct()]
            model_scan_ids.update(result_scan_ids)
            # log.debug(f"-- Results '{model.__name__:9s}' has {len(result_scan_ids):2d} scan(s) with data.")

        # log.debug(f"- {tool_name:6s} {len(model_scan_ids)=:2d} {sorted(model_scan_ids)}")

        # Secondly, gather all the scan's currently stored for this tool
        scan_ids = {scan.id for scan in Scan.select().where(Scan.tool == tool_name)}
        # log.debug(f"- {tool_name:6s} has {len(scan_ids):2d} scans on it's behalf {sorted(scan_ids)}")

        # Find any "extraneous" ones by simple set subtract (!) and delete 'em.
        scan_ids_to_delete = scan_ids - model_scan_ids
        if scan_ids_to_delete:
            # num = Scan.delete().where(Scan.id.in_(scan_ids_to_delete)).execute()
            num = 0
            msg = f"- Cleaned up {num} Scan(s) that weren't referenced."
        else:
            msg = f"Nothing done, all {tool_name.upper()} Scans have Results associated with them."
        log.debug(msg)

    for tool_name, tool_config in args.tools.items():
        if not tool_config.results_required:
            # log.debug(f"(skipping module: {tool_name} from housekeeping as data is NOT required)")
            continue
        __clean_scans(tool_name, tool_config)


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
