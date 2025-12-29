"""."""

import importlib
import logging
import sys
import types
from argparse import Namespace
from typing import Callable

from mq.tools import generate_ta_pairs, AbstractModuleConfiguration

log = logging.getLogger(__name__)


def report(args: Namespace) -> None:
    tools_analyses: list[tuple[AbstractModuleConfiguration, str]] = generate_ta_pairs(args)

    for o_tool, analysis in tools_analyses:
        try:
            report_cli: types.Module = importlib.import_module(f"{o_tool.py_module.__name__}.report_cli")
        except AttributeError as exc:
            logging.error(str(exc))
            return sys.exit(1)

        report_method: Callable = report_cli.report
        if not report_method:
            logging.error("Unable to find 'report' method in {o_tool.module_name}'s report_cli.py file!")
            return sys.exit(1)

        report_method(args, o_tool, analysis)
