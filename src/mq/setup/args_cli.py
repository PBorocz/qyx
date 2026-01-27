"""."""

import argparse

from rich_argparse import RichHelpFormatter

from mq.setup.args_configuration import setup_configuration


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
        help="Level to report on, e.g. 0 (summary), 1 (directory), 2 (file), d (derived) or h (history).",
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
