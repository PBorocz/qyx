"""Primary driver script."""

import argparse
import importlib
import sys
from argparse import Namespace
from pathlib import Path

from loguru import logger
from peewee import SqliteDatabase
from rich.traceback import install

from mq.modules import MODULE_MODELS
from mq.modules import db as db_module
from mq.modules.cloc.models import Cloc
from mq.modules.models import Project, Run
from mq.modules.radon.models import RadonRaw  # RadonCC, RadonMI, RadonHAL
from mq.modules.ruff.models import Ruff


def get_args():
    # Create parent parser with common arguments
    parser_root = argparse.ArgumentParser(add_help=False)
    parser_root.add_argument("-m", "--module", help="Module name, e.g. radon, ruff, cloc etc.")
    parser_root.add_argument("-d", "--debug", action="store_true", help="Enable debug logging.")

    parser = argparse.ArgumentParser(prog="MQ - Python Code Quality Meta Environment")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    ################################################################################
    # Ingest command
    ################################################################################
    parse_ingest = subparsers.add_parser(
        "ingest",
        parents=[parser_root],
        help="Ingest code quality results from supported tools.",
    )
    parse_ingest.add_argument(
        "-p",
        "--project",
        default=".",
        help='Base path to project to ingest from, defaults to "."',
    )
    parse_ingest.add_argument("-s", "--submodule", help="Optional sub-module, e.g. cc for Radon.")
    parse_ingest.add_argument("-v", "--verbosity", type=int, default=0, help="Logging verbosity")
    # Make module required for ingest
    parse_ingest.set_defaults(module_required=True)

    ################################################################################
    # Report command
    ################################################################################
    parse_report = subparsers.add_parser(
        "report",
        parents=[parser_root],
        help="Report on code quality for the specified (or all) projects.",
    )
    parse_report.add_argument(
        "-p",
        "--project",
        default=".",
        help='Base path to project to report for, defaults to "."',
    )
    parse_report.add_argument("-s", "--submodule", help="Optional sub-module, e.g. cc for Radon.")
    parse_report.add_argument(
        "-v",
        "--verbosity",
        type=int,
        default=0,
        help="Verbosity/depth to report (starting from 0 for top-level)",
    )
    # Make module required for report
    parse_report.set_defaults(module_required=True)

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
    models = [Run, Cloc, Ruff, RadonRaw]  # RadonCC, RadonMI, RadonHAL, RadonRAW
    db_path = Path("__data__/db.sqlite3")
    db = SqliteDatabase(db_path, pragmas={"autocommit": True, "check_same_thread": False, "foreign_keys": 1})

    # Make sure our models have tables defined for 'em!
    for model_class in [Project, Run] + MODULE_MODELS:
        model_class._meta.database = db
        model_class.create_table(safe=True)

    # db.bind(models)
    # db.connect()
    logger.debug(f"...connected to {db_path.name=} with {len(models)} models defined.")
    return db


def _setup_logging(args: Namespace) -> None:
    logger.remove()
    log_level = "DEBUG" if args.debug else "INFO"
    logger.add(
        sys.stderr,
        level=log_level,
        # format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )


def main():
    args = get_args()
    _setup_logging(args)
    db = _setup_sqlite(args)

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
            logger.error("Sorry, you must provide a valid base command to execute, use the --help option.")
            sys.exit(1)

    ################################################################################
    # Setup up our database and call the method to do our work!
    ################################################################################
    method(args, db)

    ################################################################################
    # Do any/all database housekeeping
    ################################################################################
    db_module.housekeeping(args)


if __name__ == "__main__":
    install(show_locals=True)  # Before anything else, setup rich obo tracebacks..
    main()
