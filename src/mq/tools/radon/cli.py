"""..."""

import logging
from argparse import Namespace
from importlib import import_module
from types import ModuleType
from typing import Callable

from mq.tools.base import Project, Scan, ToolType

log = logging.getLogger(__name__)


def render(args: Namespace, o_tool: ToolType, analysis: str) -> None:
    if not (project := Project.find_from_args(args)):
        log.error(f"Sorry, we didn't find any data yet for project: {args.project}")
        return None

    if not (scan := Scan.get_most_recent(project, "radon", analysis)):
        log.info(f"Sorry, we haven't performed a '{analysis}' measurement yet for this project.")
        return None

    _dispatch_level_analysis(args, o_tool, project=project, scan=scan, analysis=analysis)


def _dispatch_level_analysis(args: Namespace, o_tool, project: Project, scan: Scan, analysis: str) -> None:
    """Dispatch to the report method using the report level and sub_module requested."""
    try:
        cli_render_module_name: str = f"mq.tools.{o_tool.module}.cli_{analysis}"
        cli_render_module: ModuleType = import_module(cli_render_module_name)
    except ModuleNotFoundError:
        log.error(f"Skipping missing {cli_render_module_name=}")
        return

    method_name: str = f"{analysis}_{args.level.lower()}"
    log.debug(f"{cli_render_module=} {method_name=}")
    try:
        method: Callable = getattr(cli_render_module, method_name)
        log.debug(f"{method=}")
    except AttributeError:
        log.error(f"Sorry, invalid report level: '{args.level}', run mq report --help for valid options.")
        return

    method(args, project=project, scan=scan)
