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
            render_cli_module: types.ModuleType = o_tool.import_component("cli")
        except AttributeError as exc:
            logging.error(str(exc))
            return sys.exit(1)

        render_method: Callable = render_cli_module.render
        if not render_method:
            logging.error("Unable to find 'render' method in {o_tool.module_name}'s cli.py file!")
            return sys.exit(1)

        render_method(args, o_tool, analysis)
