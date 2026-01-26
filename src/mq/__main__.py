"""Primary driver script."""

import argparse

# from rich.traceback import install as install_traceback

from mq.cli.admin.clear import clear
from mq.cli.admin.delete import delete
from mq.cli.admin.clean import clean
from mq.cli.admin.trim import trim
from mq.cli.ingest import ingest
from mq.cli.report import report
from mq.cli.status import status
from mq.setup import setup_args, setup_logging, setup_sqlite
from mq.tools import setup_tools
from mq.web.serve import serve


def dispatch(args: argparse.Namespace) -> None:
    match args.command.lower():
        case "ingest":
            ingest(args)
        case "report":
            report(args)
        case "status":
            status(args)
        case "serve":
            serve(args)
        case "admin":
            match args.admin_command:
                case "clean":
                    clean(args)
                case "trim":
                    trim(args)
                case "clear":
                    clear(args)
                case "delete":
                    delete(args)
                case _:
                    raise RuntimeError("Sorry, invalid admin option selected, must be one of 'trim' or 'clear'")
        case _:
            raise RuntimeError("Sorry, you must provide a valid base command to execute, use the --help option.")


def main():
    # install_traceback(show_locals=False)  # Before anything else, setup colorful/informative tracebacks

    # Get/read configuration file (if any) and process all command-line arguments.
    args = setup_args()

    # Setup logging (now that we know what potential level to log to)
    setup_logging(args.log_level)

    # Setup the tools currently defined/available (and place into args)
    args.tools = setup_tools(args)

    # Setup our data-store and respective tables.
    setup_sqlite(args)

    # Lookup and dispatch the appropriate method to run based on the command (and sub-command):
    dispatch(args)

    # Do database housekeeping
    clean(args)
