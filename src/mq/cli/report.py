"""."""

import logging
import sys
import types
from argparse import Namespace
from typing import Callable

from mq.tools import generate_ta_pairs
from mq.tools.base import ToolConfig

log = logging.getLogger(__name__)


def report(args: Namespace) -> None:
    tools_analyses: list[tuple[ToolConfig, str]] = generate_ta_pairs(args)

    for o_tool, analysis in tools_analyses:
        try:
            report_cli_module: types.ModuleType = o_tool.import_component("report.cli.cli")
        except AttributeError as exc:
            logging.error(str(exc))
            return sys.exit(1)

        report_method: Callable = report_cli_module.report
        if not report_method:
            logging.error("Unable to find 'report' method in {o_tool.module_name}'s report/cli directory!")
            return sys.exit(1)

        report_method(args, o_tool, analysis)
