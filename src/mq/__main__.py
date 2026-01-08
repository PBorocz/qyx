"""Primary driver script."""

import argparse
import sys

# from rich.traceback import install as install_traceback
from rich import print

from mq import setup_logging, setup_sqlite
from mq.cli.admin.clear import clear
from mq.cli.admin.delete import delete
from mq.cli.admin.clean import clean
from mq.cli.admin.trim import trim
from mq.cli.ingest import ingest
from mq.cli.report import report
from mq.cli.status import status
from mq.tools import setup_tools, split_arg_tool_analysis
from mq.web.serve import serve


def get_args():
    """Create a command-line argument structure."""
    parser_root = argparse.ArgumentParser(add_help=False)
    parser_root.add_argument(
        "--log-level",
        default="INFO",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Set logging level",
    )

    parser = argparse.ArgumentParser(prog="MQ - python MetaQuality environment", parents=[parser_root])
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    ################################################################################
    # Status command
    ################################################################################
    parse_status = subparsers.add_parser(
        "status",
        parents=[parser_root],
        help="Report current status.",
    )
    parse_status.add_argument(
        "-l",
        "--level",
        help="Level to report on, e.g. 0 summary, 1 (detail)",
        default="0",
    )
    parse_status.add_argument(
        "-n",
        "--name",
        help="Project name, if not specified, defaults to ALL projects.",
    )

    ################################################################################
    # Ingest command
    ################################################################################
    parse_ingest = subparsers.add_parser(
        "ingest",
        parents=[parser_root],
        help="Ingest code quality results from supported tools.",
    )
    parse_ingest.add_argument(
        "-n",
        "--name",
        help="Project name, if not specified, will be determined from path.",
    )
    parse_ingest.add_argument(
        "-p",
        "--path",
        help="Path to work on, e.g. '.', '../src', '/abs/path', 'https:...').",
    )
    parse_ingest.add_argument(
        "-a",
        "--analysis",
        dest="tool_analysis",
        default=None,
        help="Analysis to run, eg. cloc, radon:cc, ruff etc.",
    )
    parse_ingest.add_argument(
        "--stdin",
        action="store_true",
        help="Read JSON from stdin instead of running command.",
    )

    ################################################################################
    # Report command
    ################################################################################
    parse_report = subparsers.add_parser(
        "report",
        parents=[parser_root],
        help="Report on code quality for the specified (or all) projects.",
    )
    parse_report.add_argument(
        "-n",
        "--name",
        help="Project name, if not specified, will be determined from path.",
    )
    parse_report.add_argument(
        "-a",
        "--analysis",
        dest="tool_analysis",
        default=None,
        help="Analysis to report on, e.g. cloc, radon:cc, ruff etc.",
    )
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
    parse_serve.add_argument("--browser", action="store_true", help="Auto-open browser", default=False)

    ################################################################################
    # Admin sub-commands
    ################################################################################
    parse_admin = subparsers.add_parser("admin", help="Administration commands")
    subparser_admin = parse_admin.add_subparsers(dest="admin_command", help="Administration subcommands")

    ################################################################################
    subparser_admin.add_parser(
        "clean",
        parents=[parser_root],
        help="Clean extraneous fluff from db",
    )

    ################################################################################
    parse_trim = subparser_admin.add_parser(
        "trim",
        parents=[parser_root],
        help="Trim old data, leaving the most recent run for each analysis",
    )
    parse_trim.add_argument("--no_confirm", action="store_true", help="Run clear *without* confirmation(!)")
    parse_trim.add_argument("-a", "--analysis", help="Analysis to trim data for, e.g. radon-cc, ruff, cloc etc.")
    # TODO: Implement this:
    # parse_trim.add_argument("-n", "--name", help='Name of project')

    ################################################################################
    parse_clear = subparser_admin.add_parser(
        "clear",
        parents=[parser_root],
        help="Clear the database, either for all analyses (default) or a specific one.",
    )
    parse_clear.add_argument("--no_confirm", action="store_true", help="Run clear *without* confirmation(!)")
    # TODO: Implement this:
    # parse_clear.add_argument("-p", "--project", default=".", help='Base path to project, defaults to "."')
    parse_clear.add_argument("-a", "--analysis", help="Optional, analysis to clear for, e.g. radon:cc, ruff, cloc etc.")

    ################################################################################
    parse_delete = subparser_admin.add_parser(
        "delete",
        parents=[parser_root],
        help="Delete a particular Project, Request or Scan.",
    )
    parse_delete.add_argument("--no_confirm", action="store_true", help="Run delete *without* confirmation(!)")
    parse_delete.add_argument("--arg", dest="delete_target", help="delete p:<id>, r:<id> or s:<id>")

    ################################################################################################
    # PARSE!!!
    ################################################################################################
    args = parser.parse_args()

    # Enforce that no command defaults to "status"
    if args.command is None:
        args.command = "status"

    # Set report options (used both by cli and web)
    d_option_defaults = dict(percentages=False, last=2)
    options_str = args.options_str if hasattr(args, "options_str") else ""
    args.options = parse_arg_option_str(options_str, d_option_defaults)

    return args


def parse_arg_option_str(options_str: str, defaults: dict = {}):
    """Parse any/all options provided (usually for reporting)."""
    opts = argparse.Namespace(**(defaults))
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
    if args.command is None:
        if not args.name and not args.path:
            print("[red]Sorry! one of either [bold]-n/--name[/bold] or  [bold]-p/--project[/bold] is required")

    if "analysis" in args:
        tool, analysis, sub = split_arg_tool_analysis(args.tool_analysis)
        if tool not in args.tools:
            s_names = ", ".join(args.tools.keys())
            print(
                f"[red]Sorry! analysis: [bold]{args.tool_analysis}[/bold] is not valid, "
                f"tool must be one of:[/red] [blue]{s_names}[/blue]",
            )
            return False
    return True


def dispatch(args: argparse.Namespace) -> None:
    match args.command:
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

    # Get/process all command-line arguments
    args = get_args()

    # Setup logging (now that we know what potential level to log to)
    setup_logging(args.log_level, False)

    # Setup the tools currently defined/available (and place into args)
    args.tools = setup_tools(args)

    # Are our arguments valid?
    if not validate_args(args):
        sys.exit(1)

    # Setup our data-store and respective tables.
    setup_sqlite(args)

    # Lookup and dispatch the appropriate method to run based on the command (and sub-command):
    dispatch(args)

    # Do database housekeeping
    clean(args)
