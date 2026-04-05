"""Group together some common queries used across tools."""

import logging
from argparse import Namespace
from importlib import import_module
from typing import Callable
from types import ModuleType

from peewee import ModelSelect

from qyx.tools._models_ import Project, Request, Scan

log = logging.getLogger(__name__)


def get_loc(args: Namespace, project: Project) -> int | None:
    """Return the lines of code obo the specific Project (based on the most recent scans available)."""
    # FIXME: Add support for SCC's uloc here as well!
    # We get LOC through either "cloc" and "Radon-Raw", try them both in order!
    from qyx.tools.cloc.models import query_cloc_0
    from qyx.tools.radon.models import query_raw_0

    cloc_scan = Scan.get_latest(project, "cloc", "cloc")
    if cloc_scan:
        result = query_cloc_0(args, cloc_scan)
        return result.lines_code

    radon_scan = Scan.get_latest(project, "radon", "raw")
    if radon_scan:
        result = query_raw_0(args, radon_scan)
        return result.sloc

    return None


def import_method(module_method: str) -> Callable + None:
    """Wrap importlib.import_module given the number of places we use it."""
    # Takes format: <module>:<method>
    # - <module> MUST exists
    # - <method> CAN exist
    (module_name, method_name) = module_method.split(":")
    # First, look up the respective module...
    try:
        module: ModuleType = import_module(module_name)
    except ImportError:
        log.critical("Sorry, can't import module: '{module_name}'!")
        return None

    # Followed by the method requested:
    try:
        return getattr(module, method_name)
    except AttributeError:
        return None


def get_scans_for_project_dimension(project: Project, dimension: str, last: int = None) -> ModelSelect:
    """Return the most recent scans for the selected project and dimension."""
    scans = (
        Scan.select()
        .join(Request)
        .where(
            Request.project == project,
            Scan.ingest_dimension == dimension,
        )
        .order_by(Scan.as_of.desc())  # IMPORTANT as we use a simple slice below to limit!
        .objects()
    )
    if last:
        scans = scans.limit(last)

    return scans
