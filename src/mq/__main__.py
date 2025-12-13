"""Primary driver script."""

import argparse
import importlib
import sys
from argparse import Namespace
from pathlib import Path

from loguru import logger
from peewee import SqliteDatabase
from rich.traceback import install as install_traceback

from mq.modules import MODULE_MODELS
from mq.modules import db as db_module
from mq.modules.models import Project, Run


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
        "-l", "--level", help="Level to report on, e.g. summary (default), detailed or full.", default="summary"
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


def _setup_sqlite(args: Namespace) -> None:
    db_path = Path("__data__/db.sqlite3")
    db = SqliteDatabase(db_path, pragmas={"autocommit": True, "check_same_thread": False, "foreign_keys": 1})

    # Make sure our models have tables defined for 'em!
    for ith, model_class in enumerate([Project, Run] + MODULE_MODELS):
        model_class._meta.database = db
        model_class.create_table(safe=True)
    logger.debug(f"...connected to {db_path.name=} with {ith + 1} models defined.")
    return db


def _setup_logging(args: Namespace) -> None:
    logger.remove()
    log_level = "DEBUG" if args.debug else "INFO"
    # TODO: For production/packaging deploy: change diagnose to False
    logger.add(sys.stderr, level=log_level, backtrace=True, diagnose=True)


def main():
    install_traceback(show_locals=False)  # Before anything else, setup rich obo tracebacks
    args = get_args()  # Get/process all command-line arguments
    _setup_logging(args)  # Setup logging (now that we know what potential level to log to)
    db = _setup_sqlite(args)  # Setup our data-store and respective tables.

    # Lookup the appropriate method to run based on the sub-command desired:
    match args.command:
        case "ingest" | "report":
            method = get_method(args.module, args.command)
            if not method:
                logger.error(f"Sorry, we don't know how to {args.command} yet on behalf of {args.module} yet!")
                return sys.exit(1)
        case "flush":
            method = db_module.flush
        case "purge":
            method = db_module.purge
        case _:
            raise RuntimeError("Sorry, you must provide a valid base command to execute, use the --help option.")

    ################################################################################
    # Dispatch to our respective method to do our work!
    ################################################################################
    method(args, db)

    ################################################################################
    # Do database housekeeping
    ################################################################################
    db_module.housekeeping(args)
