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
    """Return the most recent lines of code stat for the specific Project in preference order."""
    for loc_source in args.config.get("general.lines_of_code.sources", ()):
        tool_module, ingest_dimension, attr_s = loc_source.split(":")
        scan = Scan.get_latest(project, tool_module, ingest_dimension)
        if not scan or not scan.summary:
            continue

        # Walk down through arbitarily nested scan summary.
        value = scan.summary
        for key in attr_s.split("|"):
            value = value.get(key) if isinstance(value, dict) else None
            if value is None:
                break
        if value is not None:
            return value
    return None


def import_method(module_method: str) -> Callable | None:
    """Wrap importlib.import_module given the number of places we use it."""
    # Takes format: <module>:<method>
    # - <module> MUST exist! (if it doesn't, we raise ImportError)
    # - <method> CAN exist   (if it doesn't, we return None)
    if ":" not in module_method:
        raise ValueError("Sorry, format for import_method must be '<module>:<method>'")

    (module_name, method_name) = module_method.split(":", 1)

    try:
        # First, look up the respective module...
        module: ModuleType = import_module(module_name)
    except ImportError as exc:
        log.critical("Sorry, can't import module: '{module_name}' from {module_method=}!")
        raise exc

    try:
        # Followed by the method requested:
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
