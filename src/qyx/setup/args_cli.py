"""."""

import argparse

from rich_argparse import RichHelpFormatter

from qyx.constants import ReportLevel as Rl
from qyx.constants import StatusLevel
from qyx.setup.args_configuration import setup_configuration


################################################################################################
def get_args_command_line():
    """Read configuration file, create a command-line argument structure, parse and return the args."""
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
        prog="qyx",
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
        "-n",
        "--name",
        default="*",  # SENTINEL!
        help="Project name, if not specified, defaults to ALL projects.",
    )
    parser_status.add_argument(
        "-l",
        "--level",
        help="Level to report on, eg. g (grouped, default), i (individual scans IN DETAIL!).",
        default=StatusLevel.GROUPED,
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
        help="Project name, required to ingest data.",
    )
    parser_ingest.add_argument(
        "-p",
        "--path",
        help="Path to run analysis tool against, eg. '.', '../src', '/abs/path', 'https:...'.",
    )
    parser_ingest.add_argument(
        "-a",
        "--analysis",
        dest="analysis",
        default="*",  # SENTINEL!
        help="Analysis to ingest, eg. cloc, ruff, fxtd, cc, mi, radon etc.",
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
        default="*",  # SENTINEL!
        help="Project name, if not specified, will be determined from path.",
    )
    parser_report.add_argument(
        "-a",
        "--analysis",
        dest="analysis",
        default="*",  # SENTINEL!
        help="Analysis to run, eg. cloc, ruff, fxtd, cc, mi, radon etc.",
    )
    parser_report.add_argument(
        "-l",
        "--level",
        default=defaults.get("report_level", Rl.SUMMARY),
        help="Level to report on, eg. 0 (summary), 1 (directory), 2 (file), d (derived) or h (history).",
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
    subparser_admin = parser_admin.add_subparsers(
        dest="admin_command",
        help="Administration subcommands",
    )

    ################################################################################
    subparser_admin.add_parser(
        "clean",
        parents=[parser_root],
        help="Clean extraneous fluff from db",
        formatter_class=RichHelpFormatter,
    )

    ################################################################################
    parser_delete = subparser_admin.add_parser(
        "delete",
        parents=[parser_root],
        help="Delete a particular Project, Request or Scan.",
        formatter_class=RichHelpFormatter,
    )
    parser_delete.add_argument(
        "--no_confirm",
        action="store_true",
        help="Run delete *without* confirmation(!)",
        default=False,
    )
    parser_delete.add_argument("--target", dest="delete_target", help="delete project:<id>, request:<id> or scan:<id>")

    ################################################################################################
    # PARSE!!!
    ################################################################################################
    args = parser.parse_args(remaining_args)
    del args.config  # Don't need a handle to the potential file name provided anymore

    # Before we go, make any/all "configuration" file values available through the rest of our codebase in args!
    args.config = configuration

    return args
