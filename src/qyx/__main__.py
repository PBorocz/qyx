"""Primary driver script."""

import sys
from argparse import Namespace
from enum import Enum
from typing import Callable

# from rich.traceback import install as install_traceback

from qyx.cli.admin.delete import delete
from qyx.cli.admin.clean import clean
from qyx.cli.ingest import ingest
from qyx.cli.report import report
from qyx.cli.status import status
from qyx import constants as c
from qyx.setup.args_cli import get_args_command_line
from qyx.setup.args_interactive import get_args_interactively
from qyx.setup.args_validate import validate_args
from qyx.setup.logging import setup_logging
from qyx.setup.sqlite import setup_sqlite
from qyx.setup.tools import setup_tools
from qyx.tools._models_ import State
from qyx.web.serve import serve


def _get_dispatch_method(args: Namespace) -> Callable:
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


def dispatch(args: Namespace) -> list[str]:
    """Primary dispatch for core command requested."""
    interactive = not args.command
    first_pass = True
    commands = []
    while True:
        # If no command yet provided, go into "interactive" mode and get rest of the arguments.
        if not args.command:
            args = get_args_interactively(args, first_pass)

            # Allow user to exit interactive mode
            if args.command is None or args.command == c.EXIT_COMMAND:
                return commands

        # Are our arguments valid? (irrespective of whether they came from arguments or interactively)
        if not validate_args(args):
            # Didn't pass validation!
            if interactive:
                args.command = None  # Go back up and try again..
                continue
            else:
                sys.exit(1)  # We're done!

        # Get our ultimate run command and run it!
        commands.append(args.command)
        method = _get_dispatch_method(args)
        method(args)  # Don't care about return status, methods will warn if necessary.

        # If in command-line mode, save state and we're done!
        if not interactive:
            _update_state(args)
            return commands

        # Otherwise, reset for the next interactive cycle
        args.command = None
        first_pass = False
        print()


def _update_state(args: Namespace) -> None:
    """Update state for command-line activity."""
    kwargs = {}
    for attr in ("command", "name", "level", "dimension"):
        if attr in args and getattr(args, attr) is not None:
            value = getattr(args, attr)
            kwargs[attr] = value.value if isinstance(value, Enum) else value
    State.update(args, **kwargs)


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

    # Is our configuration valid? (we do this after tools and db are setup)
    if not args.config.validate(args):
        sys.exit(1)

    # Lookup and dispatch the appropriate method to run based on the command (and sub-command):
    cmds_run = dispatch(args)

    # Do *short* database housekeeping (if we haven't done so on explicit request above)
    if "clean" not in cmds_run:
        clean(args, vacuum=False)
