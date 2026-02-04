"""Primary driver script."""

import argparse
import sys
from typing import Callable

# from rich.traceback import install as install_traceback

from mq.cli.admin.delete import delete
from mq.cli.admin.clean import clean
from mq.cli.ingest import ingest
from mq.cli.report import report
from mq.cli.status import status
from mq.setup.args_cli import get_args_command_line
from mq.setup.args_configuration import validate_config
from mq.setup.args_interactive import get_args_interactively
from mq.setup.args_validate import validate_args
from mq.setup.logging import setup_logging
from mq.setup.sqlite import setup_sqlite
from mq.setup.tools import setup_tools
from mq.web.serve import serve
from mq.utils.state import update_state_from_args


def _get_dispatch_method(args: argparse.Namespace) -> Callable:
    match args.command.lower():
        case "ingest":
            return ingest
        case "report":
            return report
        case "status":
            return status
        case "serve":
            return serve
        case "admin":
            match args.admin_command:
                case "clean":
                    return clean
                case "delete":
                    return delete
                case _:
                    raise RuntimeError(
                        "Sorry, invalid admin option selected, must be one of 'clean' or 'delete'",
                    )
        case _:
            raise RuntimeError("Sorry, you must provide a valid base command to execute, use the --help option.")


def dispatch(args: argparse.Namespace) -> str:
    """Primary dispatch for core command requested."""
    # If no command yet provided, go into "interactive" mode and get rest of the arguments.
    if not args.command:
        args = get_args_interactively(args)

    # Are our arguments valid? (irrespective of whether they came from arguments or interactively)
    if not validate_args(args):
        sys.exit(1)

    # Is our configuration valid?
    if not validate_config(args):
        sys.exit(1)

    # Get our ultimate run command and run it!
    method_ = _get_dispatch_method(args)
    method_(args)

    # If we finished cleanly, save away the last project we worked on:
    update_state_from_args(args)

    return method_.__name__


def main():
    # install_traceback(show_locals=False)  # Before anything else, setup colorful/informative tracebacks

    # Get/read configuration file (if any) and process all *command-line* arguments.
    args = get_args_command_line()

    # Setup logging (now that we know what potential level to log to)
    setup_logging(args)

    # Find and setup the tools currently defined/available (and place into args)
    setup_tools(args)

    # Setup our data-store and respective tables.
    setup_sqlite(args)

    # Lookup and dispatch the appropriate method to run based on the command (and sub-command):
    cmd_run = dispatch(args)

    if cmd_run != "clean":
        clean(args)  # Do database housekeeping (if we haven't done so on explicit request above
