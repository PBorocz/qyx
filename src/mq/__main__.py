"""Primary driver script."""

import argparse
import sys

# from rich.traceback import install as install_traceback
from rich import print

from mq import setup_logging, setup_sqlite

from mq.cli.admin.clear import clear
from mq.cli.admin.housekeeping import housekeeping
from mq.cli.admin.trim import trim
from mq.cli.ingest import ingest
from mq.cli.report import report
from mq.cli.status import show_status
from mq.modules import setup_modules
from mq.web.server import serve


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
    parse_ingest.add_argument("--stdin", action="store_true", help="Read JSON from stdin instead of running command.")
    parse_ingest.add_argument("--git", help="Ingest historically from the specified github repo.")
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
    if args.command and args.command.lower() == "report" and hasattr(args, "options_str"):
        default_options = dict(percentages=False, last=2)
        args.options = parse_options(args.options_str or "", default_options)

    # Set defaults for the case where we don't have a command yet to execute..
    if not hasattr(args, "debug"):
        args.debug = False
    if not hasattr(args, "module"):
        args.module = None

    # If no explicit command was issued, default to simply printing a status.
    if not hasattr(args, "command") or args.command is None:
        args.command = "status"

    return args


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


def validate_args(args: argparse.Namespace) -> bool:
    """Validate arguments now that we've got everything setup."""
    if args.module and args.module not in args.modules:
        s_names = ", ".join(args.modules.keys())
        print(f"[red]Sorry! module: [bold]{args.module}[/bold] is not valid, must be one of {s_names}[/red]")
        return False

    if hasattr(args, "sub_module") and args.sub_module:
        if not args.module:
            print("[red]Sorry! can't specify a sub_module without a module itself![/red]")
            return False

        module_config = args.modules[args.module.lower()]
        if args.sub_module not in module_config.sub_modules:
            print(
                f"[red]Sorry! sub_module: [bold]{args.sub_module}[/bold] does not "
                f"exist within module: {args.module}[/red]",
            )
            return False
    return True


def main():
    # install_traceback(show_locals=False)  # Before anything else, setup colorful/informative tracebacks

    # Get/process all command-line arguments
    args = get_args()

    # Setup logging (now that we know what potential level to log to)
    setup_logging(args.debug, False)

    # Setup the modules currently defined/available (and place into args)
    args.modules = setup_modules(args)

    # Arguments read and modules defined, are our arguments valid?
    if not validate_args(args):
        sys.exit(1)

    # Setup our data-store and respective tables.
    setup_sqlite(args)

    # Lookup and dispatch the appropriate method to run based on the command (and sub-command):
    match args.command:
        case "ingest":
            ingest(args)
        case "report":
            report(args)
        case "status":
            show_status(args)
        case "serve":
            serve(args)
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

    # Do database housekeeping
    housekeeping(args)
