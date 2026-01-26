"""."""

import argparse
import logging
import sys
import yaml
from argparse import Namespace
from pathlib import Path
from platformdirs import user_config_dir
from typing import Final

from peewee import SqliteDatabase
from platformdirs import user_data_dir
from prompt_toolkit import HTML, prompt
from prompt_toolkit import print_formatted_text as ptprint
from prompt_toolkit.shortcuts import choice
from prompt_toolkit.styles import Style
from rich import print as rprint
from rich.console import Console
from rich_argparse import RichHelpFormatter
from rich.logging import RichHandler

from mq.constants import LogLevel, ReportLevel
from mq.tools import split_arg_tool_analysis
from mq.tools.base import Project, Request, Scan


COLOR_TABLE_COLUMN_1 = "#00ffff"
COLOR_TABLE_COLUMN_2 = "#00ff00"
WARNING = "#fffc00"

PROMPT_STYLE: Final = Style.from_dict(
    {
        # We use our table color scheme to match
        "prompt": COLOR_TABLE_COLUMN_1,  # Prompt is cyan
        "": COLOR_TABLE_COLUMN_2,  # User input is green
    },
)


################################################################################################
def setup_args():
    """Create a command-line argument structure, parse and return the args."""
    ################################################################################################
    # Bootstrap arg parsing for configuration file specification
    ################################################################################################
    configuration_parser, remaining_args, configuration = _setup_configuration()

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
    parser_delete.add_argument("--no_confirm", action="store_true", help="Run delete *without* confirmation(!)")
    parser_delete.add_argument("--arg", dest="delete_target", help="delete p:<id>, r:<id> or s:<id>")

    ################################################################################################
    # PARSE!!!
    ################################################################################################
    args = parser.parse_args(remaining_args)
    del args.config  # Don't need a handle to the potential file name provided anymore

    # If we didn't have any command specified, go into interactive mode!
    if not args.command:
        args = get_args(args, parser)

    # Are our arguments valid??
    if not validate_args(args):
        sys.exit(1)

    # Before we go, send the "configuration" file values through the rest of our codebase in args!
    args.config = configuration

    return args


def get_args(args: Namespace, parser) -> Namespace:
    ptprint(HTML("<green><b>Code Quality Analysis Tool</b></green>"))

    # Select command
    args.command = _select_main_command()
    match args.command:
        case "status":
            args = _prompt_command_status(args)
        case "report":
            args = _prompt_command_report(args)
        # case "ingest":
        #     args = _prompt_ingest(args)
        # case "serve":
        #     args = _prompt_serve(args)
        # case "admin":
        #     args = _prompt_admin(args)
        case "exit":
            print(
                "\n[italic]Thanks, Gracias, Merci, Danka, ありがとう, cпacи6o, Köszönöm...![/]\n",
            )
            sys.exit(0)

    ptprint()
    return args


def _select_main_command():
    """Prompt user for primary command to run."""
    options = (
        ("status", "Status - Report on current status."),
        ("report", "Report - Report on results of existing scans."),
        ("ingest", "Ingest - Ingest new scan(s) for a project."),
        ("exit", "Exit"),
    )
    return choice(message="What do you want to do?", options=options, default="status")


def _prompt_command_status(args: Namespace) -> Namespace:
    ptprint()
    args.name = _prompt_project()
    ptprint()
    args.level = _prompt_status_level()
    ptprint()
    args.log_level = _prompt_log_level()
    return args


def _prompt_command_report(args: Namespace) -> Namespace:
    ptprint()
    args.name = _prompt_project()
    ptprint()
    args.level = _prompt_report_level()
    ptprint()
    args.tool_analysis = _prompt_tool_analysis()
    ptprint()
    args.log_level = _prompt_log_level()
    return args


def _prompt_project():
    return prompt("Project name (leave blank for all) ", default="", style=PROMPT_STYLE)


def _prompt_status_level():
    options = (
        ("0", "0 - Grouped Scans (default)"),
        ("1", "1 - Individual Scans (might be a lot!)"),
    )
    return choice(message="Status Level?", options=options, default="0", style=PROMPT_STYLE)


def _prompt_report_level():
    options = [(level.value, f"{level.description}") for level in ReportLevel]
    return choice(message="Report Level of Detail?", options=options, default="0")


def _prompt_log_level():
    options = [(level.value, level.value.title()) for level in LogLevel]
    return choice(message="Log Level?", options=options, default="info")


def _prompt_tool_analysis():
    # fmt: off
    options = [
        ("cloc"      , "Count lines of code ('cloc')"),
        ("fxtd"      , "FixMe, ToDo's etc."),
        ("ruff"      , "Python linter ('ruff check')"),
        ("radon:cc"  , "Radon - Cyclomatic complexity"),
        ("radon:hal" , "Radon - Halstead metrics"),
        ("radon:mi"  , "Radon - Maintainability index"),
        ("radon:raw" , "Radon - Raw lines of code"),
    ]
    # fmt: on
    return choice(message="Analysis to report on?", options=options, default="cloc")


# def _show_form(commands, command_key: str) -> dict[str, Any] | None:
#     """Display interactive form for command options."""
#     command_config = commands[command_key]

#     # Create form panel
#     form_content = f"[bold cyan]{command_config['name']}[/bold cyan]\n"
#     if command_config.get("help"):
#         form_content += f"[dim]{command_config['help']}[/dim]\n"

#     form_panel = Panel(form_content, border_style="cyan", padding=(1, 2))
#     console.print(form_panel)
#     console.print()

#     # Create table showing all options
#     options_table = Table(
#         title="Options",
#         show_header=True,
#         header_style="bold magenta",
#         border_style="dim",
#     )
#     options_table.add_column("Option", style="cyan")
#     options_table.add_column("Type", style="yellow")
#     options_table.add_column("Default", style="green")
#     options_table.add_column("Description", style="white")

#     for opt_name, opt_config in command_config["options"].items():
#         default_val = str(opt_config.get("default", ""))
#         if opt_config.get("type") == "bool" and not opt_config.get("default"):
#             default_val = "False"
#         options_table.add_row(opt_name, opt_config["type"], default_val, opt_config.get("help", ""))

#     console.print(options_table)
#     console.print()

#     # Gather option values
#     options = {}
#     console.print("[bold]Enter values:[/bold]\n")

#     for opt_name, opt_config in command_config["options"].items():
#         value = _prompt_for_option(console, opt_name, opt_config)

#         # Allow user to cancel
#         if value is None and opt_config["type"] != "bool":
#             if not Confirm.ask("\nCancel command?", default=False):
#                 continue
#             else:
#                 return None

#         options[opt_name] = value

#     # Show summary
#     _show_summary(console, command_key, options)

#     if not Confirm.ask("\nExecute with these options?", default=True):
#         return None

#     return options


# def _prompt_for_option(console, opt_name: str, opt_config: dict) -> Any:
#     """Prompt user for a single option value based on the "type"."""
#     opt_type = opt_config["type"]
#     default = opt_config.get("default")
#     help_text = opt_config.get("help", "")

#     prompt_text = f"[cyan]{opt_name}[/cyan]"
#     if help_text:
#         prompt_text += f" [dim]({help_text})[/dim]"

#     if opt_type == "string":
#         return Prompt.ask(prompt_text, default=default or "")

#     elif opt_type == "bool":
#         return Confirm.ask(prompt_text, default=default or False)

#     elif opt_type == "choice":
#         console.print(prompt_text)
#         choices = list(opt_config["choices"])
#         return select(choices, cursor="→", cursor_style="cyan")

#     elif opt_type == "multichoice":
#         console.print(prompt_text)
#         choices = list(opt_config["choices"])
#         selected = select_multiple(choices, cursor="→", cursor_style="cyan", tick_character="✓", tick_style="green")
#         return selected if selected else default

#     elif opt_type == "list":
#         value = Prompt.ask(f"{prompt_text} [dim](space-separated)[/dim]", default="")
#         return value.split() if value else default

#     return default


# def _show_summary(console, command_key: str, options: dict[str, Any]):
#     """Display summary of selected options."""
#     summary_table = Table(
#         title="Summary",
#         show_header=True,
#         header_style="bold green",
#         border_style="green",
#     )
#     summary_table.add_column("Option", style="cyan")
#     summary_table.add_column("Value", style="yellow")

#     for key, value in options.items():
#         if isinstance(value, list):
#             value_str = ", ".join(str(v) for v in value)
#         else:
#             value_str = str(value)
#         summary_table.add_row(key, value_str)

#     console.print()
#     console.print(summary_table)


def validate_args(args: Namespace) -> bool:
    """Validate arguments now that we've got everything setup."""
    # if args.command and args.command.lower() not in ("serve", "status"):
    #     if not getattr(args, "name", None) and not getattr(args, "path", None):
    #         rprint("[red]Sorry! one of either [bold]-n/--name[/bold] or  [bold]-p/--path[/bold] is required")
    #         return False
    # Commands that deal with projects may need BOTH a name and a path, others only a name.
    if args.command.lower() == "ingest":
        if not args.name:
            rprint("[red]Sorry! [bold]-n/--name[/bold] is required to perform an ingest!")
        if not args.path and not args.stdin:
            rprint(
                "[red]Sorry! you need to either specify [bold]-p/--path[/bold] "
                "OR provide data from [bold]--stdin[/bold] to perform an ingest.",
            )
            return False

    if args.command.lower() == "report":
        if not args.name:
            rprint("[red]Sorry! [bold]-n/--name[/bold] is required to report results.")
            return False
        # --name is OPTIONAL for status command.

    if "analysis" in args:
        tool, analysis, sub = split_arg_tool_analysis(args.tool_analysis)
        if tool not in args.tools:
            s_names = ", ".join(args.tools.keys())
            rprint(
                f"[red]Sorry! analysis: [bold]{args.tool_analysis}[/bold] is not valid, "
                f"tool must be one of:[/red] [blue]{s_names}[/blue]",
            )
            return False
    return True


################################################################################################
def _setup_configuration(app_name: str = "mq") -> tuple[argparse.ArgumentParser, list[str], dict]:
    configuration_parser = argparse.ArgumentParser(add_help=False)
    configuration_parser.add_argument("-c", "--config", type=Path)
    config_args, remaining_args = configuration_parser.parse_known_args()  # Note method used here!

    if config_args.config:
        configuration = _load_config(config_args.config)
    else:
        configuration = _find_and_load_config(app_name)

    # Irrespective of which source, return the parser and configuration settings (if any!)
    return configuration_parser, remaining_args, configuration


def _load_config(config_path: Path | None) -> dict:
    """Load user's configuration from the specified path."""
    if not config_path:
        return {}

    if not config_path.exists():
        raise FileNotFoundError(f"Sorry, we couldn't find a configuration file at: {config_path}")

    with open(config_path, "rb") as fh_:
        return yaml.safe_load(fh_)


def _find_and_load_config(app_name: str, filename: str = "config.yaml") -> dict:
    """Find and load config from either of two possible locations: `cwd` and user config dir."""
    # Current directory?
    current = Path.cwd() / filename
    if current.exists():
        return _load_config(current)

    # User config directory for our app?
    config_path = Path(user_config_dir(app_name)) / filename
    if config_path.exists():
        return _load_config(config_path)

    return {}


################################################################################################
def setup_logging(arg_log_level: str, arg_peewee_debug: bool = False) -> logging.Logger:
    level = getattr(logging, arg_log_level.upper())
    peewee_level = "DEBUG" if arg_peewee_debug else "INFO"

    # Setup Rich handler
    rich_handler = RichHandler(
        console=Console(),
        show_time=True,
        show_path=True,
        rich_tracebacks=True,
        tracebacks_show_locals=False,
    )
    rich_handler.setFormatter(logging.Formatter(fmt="%(message)s", datefmt="[%X]"))

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()  # Remove any existing handlers
    root_logger.setLevel(level)
    root_logger.addHandler(rich_handler)

    # Configure uvicorn logger specifically
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.handlers.clear()  # Remove uvicorn's default handlers
    uvicorn_logger.addHandler(rich_handler)  # Replace with our nicer handler..
    uvicorn_logger.setLevel(level)
    uvicorn_logger.propagate = False  # Don't propagate to root to avoid duplicates

    # Also configure uvicorn.access if you want access logs formatted too
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.handlers.clear()
    access_logger.addHandler(rich_handler)
    access_logger.propagate = False

    # Configure Peewee logger explicitly
    peewee_logger = logging.getLogger("peewee")
    peewee_logger.handlers.clear()
    peewee_logger.addHandler(rich_handler)
    peewee_logger.setLevel(peewee_level)  # Allows us to segregate sql logging if desired.
    peewee_logger.propagate = False


################################################################################################
def setup_sqlite(args: Namespace) -> None:
    db_path = Path(user_data_dir("mq")) / "mq.sqlite3"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = SqliteDatabase(db_path, pragmas={"autocommit": True, "check_same_thread": False, "foreign_keys": 1})

    # Make sure our models have tables defined for 'em!
    models = [Project, Request, Scan]
    for configuration in args.tools.values():
        for tool_peewee_class in configuration.models.values():
            models.append(tool_peewee_class)

    for model_class in models:
        model_class._meta.database = db
        model_class.create_table(safe=True)

    log = logging.getLogger(__name__)
    log.debug(f"...connected to {db_path.name=} with {len(models)} models defined.")
