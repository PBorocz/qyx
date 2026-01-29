"""."""

import logging
from argparse import Namespace

from mq.tools import generate_ta_pairs
from mq.tools.base import ToolConfig

log = logging.getLogger(__name__)


def report(args: Namespace) -> None:
    tools_analyses: list[tuple[ToolConfig, str]] = generate_ta_pairs(args)

    for o_tool, analysis in tools_analyses:
        o_tool.render_cli_method(args, o_tool, analysis)
