"""Primary driver script."""

import argparse
import importlib
import sys


from loguru import logger
from rich.traceback import install as install_traceback

from mq.serve import run_server
from mq import setup_logging, setup_sqlite
from mq.db import flush, housekeeping, purge


def get_args():
    # Create parent parser with common arguments
    parser_root = argparse.ArgumentParser(add_help=False)
    parser_root.add_argument("-m", "--module", help="Module name, e.g. radon, ruff, cloc etc.")
    parser_root.add_argument("-p", "--project", default=".", help='Base path to project, defaults to "."')
    parser_root.add_argument("-d", "--debug", action="store_true", help="Enable debug logging.", default=False)

    parser = argparse.ArgumentParser(prog="MQ - python MetaQuality environment")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    ################################################################################
    # Ingest command
    ################################################################################
    parse_serve = subparsers.add_parser(
        "serve",
        parents=[parser_root],
        help="Run built-in web server for reporting.",
    )
    parse_serve.add_argument("--port", help="Optional port, default is 5011.", default=5011)
    parse_serve.add_argument("--no-browser", action="store_true", help="Don't auto-open browser")

    ################################################################################
    # Ingest command
    ################################################################################
    parse_ingest = subparsers.add_parser(
        "ingest",
        parents=[parser_root],
        help="Ingest code quality results from supported tools.",
    )
    parse_ingest.add_argument("-s", "--sub_module", help="Optional sub-module, e.g. cc, hal, mi or raw for Radon.")
    parse_ingest.add_argument("-v", "--verbosity", type=int, default=0, help="Logging verbosity")
    parse_ingest.set_defaults(module_required=True)  # Make module required for ingest

    ################################################################################
    # Report command
    ################################################################################
    parse_report = subparsers.add_parser(
        "report",
        parents=[parser_root],
        help="Report on code quality for the specified (or all) projects.",
    )
    parse_report.set_defaults(module_required=True)  # Make module required for report (...for now)
    parse_report.add_argument("-s", "--sub_module", help="Optional sub-module (if applicable, e.g. cc for Radon).")
    parse_report.add_argument("--last", type=int, help="Report on last <n> weeks of history.")
    parse_report.add_argument(
        "-l",
        "--level",
        help="Level to report on, e.g. summary (default), detail or full.",
        default="summary",
    )

    ################################################################################
    # Flush command
    ################################################################################
    subparsers.add_parser(
        "flush",
        parents=[parser_root],
        help="Flush store either for all or specified modules.",
    )

    ################################################################################
    # Purge command
    ################################################################################
    subparsers.add_parser(
        "purge",
        parents=[parser_root],
        help="Purge store either for all or specified modules, leaving the most recent run",
    )

    args = parser.parse_args()

    # Set defaults for the case where we don't have a command yet to execute..
    if not hasattr(args, "debug"):
        args.debug = False
    if not hasattr(args, "module"):
        args.module = None

    # TODO: Ensure here that a valid sub_module has been provided (from MODULES_AND_MODELS)
    # TODO: Ensure here that a valid level has been provided..

    # We want a command for now!
    if not hasattr(args, "command") or args.command is None:
        print("Sorry, please specify a command:\n")
        parser.print_help()
        sys.exit(1)

    # Check if module is required for certain commands
    if hasattr(args, "module_required") and args.module_required and not args.module:
        parser.error(f"The {args.command} command requires --module argument")

    return args


def get_method(module: str, method: str):
    try:
        module_path = f"mq.modules.{module}.{method}"  # Construct the path to the specific
        module = importlib.import_module(module_path)  # .py file in the respective module and import it.
        return getattr(module, method)  # Return the method from the module

    except ImportError as e:
        logger.error(f"Could not import {module_path}: {e}")
        return None
    except AttributeError as e:
        logger.error(f"Method {method} not found in {module_path}: {e}")
        return None


def main():
    install_traceback(show_locals=False)  # Before anything else, setup rich obo tracebacks
    args = get_args()  # Get/process all command-line arguments
    setup_logging(args, logger)  # Setup logging (now that we know what potential level to log to)
    setup_sqlite(args, logger)  # Setup our data-store and respective tables.

    # Lookup the appropriate method to run based on the sub-command desired:
    match args.command:
        case "ingest" | "report":
            method = get_method(args.module, args.command)
            if not method:
                logger.error(f"Sorry, we don't know how to {args.command} yet on behalf of {args.module} yet!")
                return sys.exit(1)
        case "serve":
            method = run_server
        case "flush":
            method = flush
        case "purge":
            method = purge
        case _:
            raise RuntimeError("Sorry, you must provide a valid base command to execute, use the --help option.")

    ################################################################################
    # Dispatch to our respective method to do our work!
    ################################################################################
    method(args)

    ################################################################################
    # Do database housekeeping
    ################################################################################
    housekeeping(args)
