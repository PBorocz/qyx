"""."""

import logging

from argparse import Namespace
import sys

from mq.cli import get_method

log = logging.getLogger(__name__)


def report(args: Namespace) -> None:
    def __do_report(module: str) -> None:
        method, msg = get_method(module, "report_cli", "report")
        if not method and msg:
            logging.error(msg)
            return sys.exit(1)
        method(args)

    if args.module:
        # Single report request, lookup the method and do it!
        __do_report(args.module)
    else:
        # Report over ALL available modules..
        for module in args.modules.keys():
            __do_report(module)
