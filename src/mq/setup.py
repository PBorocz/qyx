"""."""

import argparse
import logging
import sys
import yaml
from argparse import Namespace
from pathlib import Path
from platformdirs import user_config_dir

from questionary import Style, Choice, confirm, select, text
from questionary import print as qprint

from peewee import SqliteDatabase
from platformdirs import user_data_dir
from rich import print as rprint
from rich.console import Console
from rich_argparse import RichHelpFormatter
from rich.logging import RichHandler

from mq.constants import BaseModel, ReportLevel, StatusLevel
from mq.tools import split_arg_tool_analysis
from mq.tools.base import Project, Request, Scan
from mq.utils.state import load_state

# fmt: off
PROMPT_STYLE = Style([
    # ('qmark'       , 'fg:#00d7ff bold' ), # Question mark
    # ('question'    , 'fg:#ffffff bold' ), # Question text
    # ('answer'      , 'fg:#00ff87 bold' ), # Selected answer
    # ('selected'    , 'fg:#00ff87'      ), # Selected (in checkbox)
    # ('pointer'     , 'fg:#00ff87 bold' ), # Selection pointer
    # ('highlighted' , 'fg:#00ff87'      ), # Highlighted choice
    # ('instruction' , 'fg:#888888'      ), # Instructions
])
# fmt: on


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
    def _goodbye():
        qprint(
            "\nThanks, gracias, merci, danka, ありがとう, cпacи6o, köszönöm...!",
            style="bold italic fg:green",
        )
        sys.exit(0)

    qprint("Code Quality Analysis Tool\n", style="bold italic fg:cyan")

    # Select command
    args.command = _select_main_command()
    match args.command.lower():
        case "status":
            args = _prompt_command_status(args)
        case "report":
            args = _prompt_command_report(args)
        case "ingest":
            args = _prompt_command_ingest(args)
        case "serve":
            args = _prompt_command_serve(args)
        case "admin":
            args = _prompt_command_admin(args)
            if not args:
                _goodbye()
        case "exit":
            _goodbye()

    return args


def _select_main_command():
    """Prompt user for primary command to run."""
    # fmt: off
    choices = [
        Choice(title="Status - Display current status"                     , value="status" , shortcut_key="s"),
        Choice(title="Report - Report on results of existing scans"        , value="report" , shortcut_key="r"),
        Choice(title="Ingest - Ingest new scan(s) for a project"           , value="ingest" , shortcut_key="i"),
        Choice(title="Serve  - Run built-in web server to display reports" , value="serve"  , shortcut_key="v"),
        Choice(title="Admin  - Access administrative functions"            , value="admin"  , shortcut_key="a"),
        Choice(title="Exit"                                                , value="exit"   , shortcut_key="x"),
    ]
    # fmt: on

    return select(
        "Select command:",
        choices=choices,
        style=PROMPT_STYLE,
        use_indicator=True,
        use_emacs_keys=True,
    ).ask()


################################################################################################
def _prompt_command_status(args: Namespace) -> Namespace:
    args.name = _prompt_name()
    args.level = _prompt_status_level()
    return args


def _prompt_command_report(args: Namespace) -> Namespace:
    args.name = _prompt_name()
    args.level = _prompt_report_level()
    args.tool_analysis = _prompt_tool_analysis()
    return args


def _prompt_command_ingest(args: Namespace) -> Namespace:
    args.name = _prompt_name()
    args.path = _prompt_path()
    args.tool_analysis = _prompt_tool_analysis()
    args.stdin = False  # Obviously since we're not able to read from stdin interactively!
    return args


def _prompt_command_serve(args: Namespace) -> Namespace:
    args.port = _prompt_port()
    args.browser = _prompt_browser()
    return args


def _prompt_command_admin(args: Namespace) -> Namespace:
    """Prompt user for primary command to run."""
    choices = [
        Choice(
            title="Delete a particular Scan, Request or entire Project",
            value="delete",
            shortcut_key="d",
        ),
        # Choice(
        #     title="Clean extraneous fluff from data store",
        #     value="clean",
        #     shortcut_key="c",
        #     disabled=True,
        # ),
        # Choice(
        #     title="Trim old data, leaving most recent run for each analysis",
        #     value="trim",
        #     shortcut_key="t",
        #     disabled=True,
        # ),
        # Choice(
        #     title="Clear the database, either for all analyses or a specific one",
        #     value="clear",
        #     shortcut_key="l",
        #     disabled=True,
        # ),
    ]

    args.admin_command = select(
        "Select administration command:",
        choices=choices,
        style=PROMPT_STYLE,
        use_indicator=True,
        use_emacs_keys=True,
    ).ask()

    match args.admin_command:
        case "delete":
            args = _prompt_admin_command_delete(args)
        # case "clean":
        #     args = _prompt_admin_command_clean(args)
        # case "trim":
        #     args = _prompt_admin_command_trim(args)
        # case "clear":
        #     args = _prompt_admin_command_clear(args)
    return args


def _prompt_admin_command_delete(args: Namespace) -> Namespace:
    delete_entity: BaseModel = _prompt_delete_entity()
    delete_id: int = _prompt_delete_id(delete_entity)
    args.delete_target: str = f"{delete_entity.value}:{delete_id}"
    args.no_confirm: bool = False  # Let the delete commmand itself do the confirmation.
    return args


################################################################################################
def _prompt_name():
    state = load_state()
    kwargs = dict()
    if last_name := state.get("last_name"):
        kwargs["default"] = last_name

    return text("Project name (leave blank for all)?", style=PROMPT_STYLE, **kwargs).ask()


def _prompt_path():
    return text("Project path (either <dir> or <gitRepo>?", default="", style=PROMPT_STYLE).ask()


def _prompt_port() -> int:
    port = text(
        "Port to run on?",
        default="5011",
        style=PROMPT_STYLE,
        validate=lambda port: port.isdigit()
        and (1024 <= int(port) <= 65535)
        or "Please enter a port number between 1024 and 65535",
    ).ask()
    return int(port)


def _prompt_browser() -> str:
    return confirm("Auto-open browser?", default=False, style=PROMPT_STYLE).ask()


def _prompt_delete_entity() -> BaseModel:
    choices = [Choice(title=model.value.title(), value=model.value) for model in BaseModel]
    value = select(
        "What entity do you want to delete?",
        choices=choices,
        style=PROMPT_STYLE,
        use_indicator=True,
        use_emacs_keys=True,
    ).ask()
    return BaseModel(value)


def _prompt_delete_id(delete_entity: BaseModel) -> int:
    value = text(
        f"Enter database id of the {delete_entity.title()} you want to delete:",
        style=PROMPT_STYLE,
        validate=lambda text: text.isdigit() or "Please enter a valid integer database id",
    ).ask()
    return int(value)


def _prompt_status_level() -> StatusLevel:
    choices = [Choice(title=level.description, value=level.value) for level in StatusLevel]
    value = select(
        "Status Level?",
        choices=choices,
        default=choices[0],
        style=PROMPT_STYLE,
        use_indicator=True,
        use_emacs_keys=True,
    ).ask()
    return StatusLevel(value)


def _prompt_report_level() -> ReportLevel:
    choices = [Choice(title=level.description, value=level.value) for level in ReportLevel]
    value = select(
        message="Report Level of Detail?",
        choices=choices,
        default=ReportLevel.SUMMARY,
        style=PROMPT_STYLE,
    ).ask()
    return ReportLevel(value)


def _prompt_tool_analysis():
    # fmt: off
    state = load_state()
    kwargs = dict()
    if last_tool_analysis := state.get("last_tool_analysis"):
        kwargs["default"] = last_tool_analysis
    choices = [
        Choice(title="Count lines of code ('cloc')"  , value="cloc"      ),
        Choice(title="FixMe, ToDo's etc."            , value="fxtd"      ),
        Choice(title="Python linter ('ruff check')"  , value="ruff"      ),
        Choice(title="Radon - Cyclomatic complexity" , value="radon:cc"  ),
        Choice(title="Radon - Halstead metrics"      , value="radon:hal" ),
        Choice(title="Radon - Maintainability index" , value="radon:mi"  ),
        Choice(title="Radon - Raw lines of code"     , value="radon:raw" ),
    ]
    # fmt: on
    return select(message="Analysis to report on?", choices=choices, style=PROMPT_STYLE, **kwargs).ask()


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
