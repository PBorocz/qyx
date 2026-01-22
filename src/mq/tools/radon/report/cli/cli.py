"""..."""

import logging
import sys
import types
from argparse import Namespace
from importlib import import_module
from typing import Callable

from mq.tools.base import Project, Scan

log = logging.getLogger(__name__)

RADON_SUB_TOOLS = ("raw", "mi", "hal", "cc")


def report(args: Namespace, o_tool, analysis: str) -> None:
    if not (project := Project.find_from_args(args)):
        log.error(f"Sorry, we didn't find any data yet for project: {args.project}")
        return None

    if not (scan := Scan.get_most_recent(project, "radon", analysis)):
        log.info(f"Sorry, we haven't performed a {args.sub_module} measurement yet for this project.")
        return None

    _dispatch_level_submodule(args, o_tool, project=project, scan=scan, analysis=analysis)


def _dispatch_level_submodule(args: Namespace, o_tool, project: Project, scan: Scan, analysis: str) -> None:
    """Dispatch to the report method using the report level and sub_module requested."""
    report_module = import_module(f"mq.tools.{o_tool.module_name}.report.cli.{analysis}_{args.level.lower()}")
    method_name: str = f"{analysis}_{args.level.lower()}"
    log.debug(f"{report_module=} {method_name=}")
    try:
        method: Callable = getattr(report_module, method_name)
        log.debug(f"{method=}")
    except AttributeError:
        log.error(f"Sorry, invalid report level: '{args.level}', run mq report --help for valid options.")
        return

    method(project=project, scan=scan)
