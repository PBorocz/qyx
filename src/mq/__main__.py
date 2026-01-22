"""Primary driver script."""

import argparse
import sys

# from rich.traceback import install as install_traceback
from rich import print
from rich_argparse import RawDescriptionRichHelpFormatter, RichHelpFormatter

from mq import setup_configuration, setup_logging, setup_sqlite
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
    ################################################################################################
    # Bootstrap arg parsing for configuration file specification
    ################################################################################################
    configuration_parser, remaining_args, configuration = setup_configuration()

    ################################################################################################
    # Primary arg parsing: Setup a root/parent parser (from which child command parser will come)
    ################################################################################################
    defaults = configuration.get("command_line_defaults", {})
    parser_root = argparse.ArgumentParser(
        add_help=False,
        parents=[configuration_parser],
    )
    parser_root.add_argument(
        "--log-level",
        default=defaults.get("log_level", "info"),
        choices=["debug", "info", "warning", "error", "critical"],
        help="Set logging level",
    )
    parser = argparse.ArgumentParser(
        prog="mq",
        parents=[parser_root],
        formatter_class=RichHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    ################################################################################
    # Status command
    ################################################################################
    parser_status = subparsers.add_parser(
        "status",
        parents=[parser_root],
        help="Report current status.",
        formatter_class=RichHelpFormatter,
    )
    parser_status.add_argument(
        "-l",
        "--level",
        help="Level to report on, e.g. 0 (summary), 1 (usually directory) or 2 (usually file).",
        default=defaults.get("level", "0"),
    )
    parser_status.add_argument(
        "-n",
        "--name",
        default=defaults.get("name"),
        help="Project name, if not specified, defaults to ALL projects.",
    )

    ################################################################################
    # Ingest command
    ################################################################################
    parser_ingest = subparsers.add_parser(
        "ingest",
        parents=[parser_root],
        help="Ingest code quality results for a specific project.",
        formatter_class=RichHelpFormatter,
    )
    parser_ingest.add_argument(
        "-n",
        "--name",
        default=defaults.get("name"),
        help="Project name, required to ingest data.",
    )
    parser_ingest.add_argument(
        "-p",
        "--path",
        default=defaults.get("path"),
        help="Path to run analysis tool against, eg. '.', '../src', '/abs/path', 'https:...'.",
    )
    parser_ingest.add_argument(
        "-a",
        "--analysis",
        dest="tool_analysis",
        help="Tool & analysis to run, eg. cloc, radon:cc, ruff etc.",
    )
    parser_ingest.add_argument(
        "--stdin",
        action="store_true",
        help="Read JSON from stdin instead of running ingest command (--path not required)",
    )

    ################################################################################
    # Report command
    ################################################################################
    parser_report = subparsers.add_parser(
        "report",
        parents=[parser_root],
        help="Report on code quality for the specified (or all) projects.",
        formatter_class=RichHelpFormatter,
    )
    parser_report.add_argument(
        "-n",
        "--name",
        default=defaults.get("name"),
        help="Project name, if not specified, will be determined from path.",
    )
    parser_report.add_argument(
        "-a",
        "--analysis",
        dest="tool_analysis",
        help="Analysis to report on, e.g. cloc, radon:cc, ruff etc.",
    )
    parser_report.add_argument(
        "-l",
        "--level",
        help="Level to report on, e.g. 0 (summary & default), 1 (detail), 2 (full) or h (history).",
        default=defaults.get("level", "0"),
    )

    ################################################################################
    # Serve command
    ################################################################################
    parser_serve = subparsers.add_parser(
        "serve",
        parents=[parser_root],
        help="Run built-in web server for reporting.",
        formatter_class=RichHelpFormatter,
    )
    parser_serve.add_argument(
        "--port",
        help="Optional port, default is 5011.",
        default=defaults.get("port", "5011"),
    )
    parser_serve.add_argument(
        "--browser",
        action="store_true",
        help="Auto-open browser",
        default=defaults.get("browser", False),
    )

    ################################################################################
    # Admin sub-commands
    ################################################################################
    parser_admin = subparsers.add_parser(
        "admin",
        help="Administration commands",
        formatter_class=RichHelpFormatter,
    )
    subparser_admin = parser_admin.add_subparsers(dest="admin_command", help="Administration subcommands")

    ################################################################################
    subparser_admin.add_parser(
        "clean",
        parents=[parser_root],
        help="Clean extraneous fluff from db",
        formatter_class=RichHelpFormatter,
    )

    ################################################################################
    parser_trim = subparser_admin.add_parser(
        "trim",
        parents=[parser_root],
        help="Trim old data, leaving the most recent run for each analysis",
        formatter_class=RichHelpFormatter,
    )
    parser_trim.add_argument("--no_confirm", action="store_true", help="Run clear *without* confirmation(!)")
    parser_trim.add_argument("-a", "--analysis", help="Analysis to trim data for, e.g. radon-cc, ruff, cloc etc.")
    # TODO: Implement this:
    # parse_trim.add_argument("-n", "--name", help='Name of project')

    ################################################################################
    parser_clear = subparser_admin.add_parser(
        "clear",
        parents=[parser_root],
        help="Clear the database, either for all analyses (default) or a specific one.",
        formatter_class=RichHelpFormatter,
    )
    parser_clear.add_argument("--no_confirm", action="store_true", help="Run clear *without* confirmation(!)")
    parser_clear.add_argument("-a", "--analysis", help="Optional, analysis clear, e.g. radon:cc, ruff, cloc etc.")
    # TODO: Implement this:
    # parser_clear.add_argument("-p", "--project", default=".", help='Base path to project, defaults to "."')

    ################################################################################
    parser_delete = subparser_admin.add_parser(
        "delete",
        parents=[parser_root],
        help="Delete a particular Project, Request or Scan.",
        formatter_class=RichHelpFormatter,
    )
    parser_delete.add_argument("--no_confirm", action="store_true", help="Run delete *without* confirmation(!)")
    parser_delete.add_argument("--arg", dest="delete_target", help="delete p:<id>, r:<id> or s:<id>")

    ################################################################################################
    # PARSE!!!
    ################################################################################################
    args = parser.parse_args(remaining_args)

    # Before we go, send the "configuration" file values through the rest of our codebase in args!
    args.config = configuration
    return args


def validate_args(args: argparse.Namespace) -> bool:
    """Validate arguments now that we've got everything setup."""
    if args.command and args.command.lower() not in ("serve"):
        if not getattr(args, "name", None) and not getattr(args, "path", None):
            print("[red]Sorry! one of either [bold]-n/--name[/bold] or  [bold]-p/--path[/bold] is required")
            return False

    # Commands that deal with projects may need BOTH a name and a path, others only a name.
    if args.command.lower() == "ingest":
        if not args.name:
            print("[red]Sorry! [bold]-n/--name[/bold] is required to perform an ingest!")
        if not args.path and not args.stdin:
            print(
                "[red]Sorry! you need to either specify [bold]-p/--path[/bold] "
                "OR provide data from [bold]--stdin[/bold] to perform an ingest.",
            )
            return False

    if args.command.lower() == "report":
        if not args.name:
            print("[red]Sorry! [bold]-n/--name[/bold] is required to report results.")
            return False
        # --name is OPTIONAL for status command.

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

    # Get/read configuration file (if any) and process all command-line arguments.
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
