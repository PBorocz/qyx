"""Primary driver script."""

import argparse
import importlib
import logging
import sys
from typing import Callable

# from rich.traceback import install as install_traceback

from mq import setup_logging, setup_sqlite
from mq.modules import MODULE_NAMES

from mq.utils.db import clear, housekeeping, trim
from mq.cli.status import status
from mq.web.server import run_server


def get_args():
    # Create parent parser with common arguments
    parser_root = argparse.ArgumentParser(add_help=False)
    parser_root.add_argument("-d", "--debug", action="store_true", help="Enable debug logging.", default=False)

    parser = argparse.ArgumentParser(prog="MQ - python MetaQuality environment")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    ################################################################################
    # Status command
    ################################################################################
    subparsers.add_parser(
        "status",
        parents=[parser_root],
        help="Report current status for all or specific project.",
    )

    ################################################################################
    # Ingest command
    ################################################################################
    parse_ingest = subparsers.add_parser(
        "ingest",
        parents=[parser_root],
        help="Ingest code quality results from supported tools.",
    )
    parse_ingest.add_argument("-p", "--project", default=".", help='Base path to project, defaults to "."')
    parse_ingest.add_argument("-m", "--module", help="Module name, e.g. radon, ruff, cloc etc.")
    parse_ingest.add_argument("-s", "--sub_module", help="Optional sub-module, e.g. cc, hal, mi or raw for Radon.")
    parse_ingest.add_argument("--stdin", action="store_true", help="Read JSON from stdin instead of running subprocess")
    parse_ingest.add_argument("--git", help="Ingest from a github repo")
    parse_ingest.add_argument("-v", "--verbosity", type=int, default=0, help="Logging verbosity")

    ################################################################################
    # Report command
    ################################################################################
    parse_report = subparsers.add_parser(
        "report",
        parents=[parser_root],
        help="Report on code quality for the specified (or all) projects.",
    )
    parse_report.add_argument("-p", "--project", default=".", help='Base path to project, defaults to "."')
    parse_report.add_argument("-m", "--module", help="Module name, e.g. radon, ruff, cloc etc.")
    parse_report.add_argument("-s", "--sub_module", help="Optional sub-module (if applicable, e.g. cc for Radon).")
    parse_report.add_argument(
        "-o",
        "--options",
        help="Report option(s), eg. 'last:5,percentage' etc.",
        type=str,
        dest="options_str",
        default="",
    )
    parse_report.add_argument(
        "-l",
        "--level",
        help="Level to report on, e.g. 0 (summary & default), 1 (detail), 2 (full) or h (history).",
        default="0",
    )

    ################################################################################
    # Serve command
    ################################################################################
    parse_serve = subparsers.add_parser(
        "serve",
        parents=[parser_root],
        help="Run built-in web server for reporting.",
    )
    parse_serve.add_argument("--port", help="Optional port, default is 5011.", default=5011)
    parse_serve.add_argument("--nobrowser", action="store_true", help="Don't auto-open browser")

    ################################################################################
    # Admin command
    ################################################################################
    parse_admin = subparsers.add_parser("admin", help="Administration commands")
    subparser_admin = parse_admin.add_subparsers(dest="admin_command", help="Administration subcommands")

    parse_trim = subparser_admin.add_parser(
        "trim",
        parents=[parser_root],
        help="Trim old data, leaving the most recent run for each module",
    )
    parse_trim.add_argument("--no_confirm", action="store_true", help="Run clear *without* confirmation(!)")
    parse_trim.add_argument("-m", "--module", help="Module name, e.g. radon, ruff, cloc etc.")
    # TODO: Implement this:
    # parse_trim.add_argument("-p", "--project", default=".", help='Base path to project, defaults to "."')

    parse_clear = subparser_admin.add_parser(
        "clear",
        parents=[parser_root],
        help="Clear the database, either for all modules (default) or a specified module.",
    )
    parse_clear.add_argument("--no_confirm", action="store_true", help="Run clear *without* confirmation(!)")
    parse_clear.add_argument("-p", "--project", default=".", help='Base path to project, defaults to "."')
    parse_clear.add_argument("-m", "--module", help="Module name, e.g. radon, ruff, cloc etc.")

    ################################################################################################
    # PARSE!!!
    ################################################################################################
    args = parser.parse_args()

    # Parse any REPORT options provided and add into the args
    if args.command.lower() == "report" and hasattr(args, "options_str"):
        default_options = dict(percentages=False, last=2)
        args.options = parse_options(args.options_str or "", default_options)

    # Set defaults for the case where we don't have a command yet to execute..
    if not hasattr(args, "debug"):
        args.debug = False
    if not hasattr(args, "module"):
        args.module = None

    # TODO: Ensure here that a valid sub_module has been provided (from MODULES_AND_MODELS)

    # TODO: Ensure here that a valid level has been provided..

    # If no explicit command was issued, default to simply printing a status.
    if not hasattr(args, "command") or args.command is None:
        args.command = "status"

    return args


def get_method(module_dir: str, py_filename: str, method: str) -> tuple[Callable | None, str | None]:
    module_path = f"mq.modules.{module_dir}.{py_filename}"  # Construct the path to the specific .py file
    logging.debug(f"Using {module_path=}")
    try:
        module = importlib.import_module(module_path)  # ...and import it.
    except ImportError as e:
        return None, f"Could not import {module_path}: {e}"

    try:
        return getattr(module, method), None  # Return the method from the module
    except AttributeError as e:
        return None, f"Method {method} not found in {module_path}: {e}"


def _dispatch_ingest(args: argparse.Namespace) -> None:
    def __do_ingest(module: str) -> None:
        method, msg = get_method(module, "ingest", "ingest")
        if not method and msg:
            logging.error(msg)
            return sys.exit(1)
        method(args)

    if args.module:
        # Single ingest request, lookup the method and do it!
        __do_ingest(args.module)
    else:
        # Ingest over ALL available modules..
        for module in MODULE_NAMES:
            __do_ingest(module)


def _dispatch_report(args: argparse.Namespace) -> None:
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
        for module in MODULE_NAMES:
            __do_report(module)


def parse_options(options_str: str, defaults=None):
    """Parse any/all options provided (usually for reporting)."""
    opts = argparse.Namespace(**(defaults or {}))
    if not options_str:
        return opts

    for item in options_str.split(","):
        if ":" in item:
            key, value = item.split(":", 1)
            try:
                value = int(value)
            except ValueError:
                ...
            setattr(opts, key, value)
        else:
            # Boolean flag
            setattr(opts, item, True)

    return opts


def main():
    # install_traceback(show_locals=False)  # Before anything else, setup rich obo tracebacks
    args = get_args()  # Get/process all command-line arguments
    setup_logging(args.debug, False)  # Setup logging (now that we know what potential level to log to)
    setup_sqlite(args)  # Setup our data-store and respective tables.

    # Lookup the appropriate method to run based on the sub-command desired:
    match args.command:
        case "ingest":
            _dispatch_ingest(args)
        case "report":
            _dispatch_report(args)
        case "status":
            status(args)
        case "serve":
            run_server(args)
        case "admin":
            match args.admin_command:
                case "trim":
                    trim(args)
                case "clear":
                    clear(args)
                case _:
                    raise RuntimeError("Sorry, invalid admin option selected, must be one of 'trim' or 'clear'")
        case _:
            raise RuntimeError("Sorry, you must provide a valid base command to execute, use the --help option.")

    housekeeping(args)  # Do database housekeeping
