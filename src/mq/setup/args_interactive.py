"""."""

import sys
from argparse import Namespace

from questionary import Style, Choice, confirm, path, select, text
from questionary import print as qprint

from mq.constants import BaseModel, ReportLevel, StatusLevel
from mq.tools.base import Project
from mq.utils.state import load_state

# fmt: off
PROMPT_STYLE = Style([
    ('pointer'     , 'fg:#00ff87 bold' ), # Selection pointer
    ('highlighted' , 'fg:#00ff87'      ), # Highlighted choice
    # ('qmark'       , 'fg:#00d7ff bold' ), # Question mark
    # ('question'    , 'fg:#ffffff bold' ), # Question text
    # ('answer'      , 'fg:#00ff87 bold' ), # Selected answer
    # ('selected'    , 'fg:#00ff87'      ), # Selected (in checkbox)
    # ('instruction' , 'fg:#888888'      ), # Instructions
])
# fmt: on


def get_args_interactively(args: Namespace) -> Namespace:
    def _goodbye():
        qprint(
            "\nThanks, gracias, merci, danka, ありがとう, cпacи6o, köszönöm...!",
            style="bold italic fg:green",
        )
        sys.exit(0)

    qprint("Code Quality Analysis Tool\n", style="bold italic fg:cyan")

    # Select command
    try:
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
    except KeyboardInterrupt:
        qprint("Ok...nothing done.")
        _goodbye()

    qprint("")  # Add an extra line to demarcate whatever comes below...
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
        "Command",
        choices=choices,
        style=PROMPT_STYLE,
        use_indicator=True,
        use_emacs_keys=True,
    ).unsafe_ask()


################################################################################################
def _prompt_command_status(args: Namespace) -> Namespace:
    args.name = _prompt_existing_name()
    args.level = _prompt_status_level()
    return args


def _prompt_command_report(args: Namespace) -> Namespace:
    args.name = _prompt_existing_name()
    args.tool_analysis = _prompt_tool_analysis(args, "Analysis")
    args.level = _prompt_report_level()
    return args


def _prompt_command_ingest(args: Namespace) -> Namespace:
    args.name, args.path = _prompt_name_path()
    args.tool_analysis = _prompt_tool_analysis(args, "Analysis")
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
        Choice(
            title="Run database housekeeping, ie. clean extraneous fluff from data store",
            value="clean",
            shortcut_key="c",
        ),
    ]

    args.admin_command = select(
        "Administration command",
        choices=choices,
        style=PROMPT_STYLE,
        use_indicator=True,
        use_emacs_keys=True,
    ).unsafe_ask()

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
def _prompt_existing_name(include_new_option: bool = False):
    state = load_state()
    choices = []
    kwargs = dict()
    for project in Project.select():
        if state.get("last_name") and project.name.lower() == state.get("last_name").lower():
            kwargs["default"] = project.name
        choices.append(Choice(title=project.name))
    if include_new_option:
        choices.append(Choice(title="-New Project-", value="__new__"))

    project = select(
        "Project",
        choices=choices,
        style=PROMPT_STYLE,
        use_indicator=True,
        use_emacs_keys=True,
        **kwargs,
    ).unsafe_ask()
    return project


def _prompt_name_path() -> tuple[str, str]:
    """Prompt for either an existing project or a new one, if new, get name and path."""
    project_name = _prompt_existing_name(include_new_option=True)

    # New project! Where from?
    choices = [
        Choice(title="File path", value="f"),
        Choice(title="Git repo", value="g"),
    ]
    source = select(
        "Source to ingest from",
        choices=choices,
        style=PROMPT_STYLE,
        use_indicator=True,
        use_emacs_keys=True,
    ).unsafe_ask()

    match source:
        case "f":
            path_ = path("Path", style=PROMPT_STYLE, only_directories=True).unsafe_ask()
        case "g":
            path_ = text("Git repo URL", style=PROMPT_STYLE).unsafe_ask()

    if project_name == "__new__":
        project_name = text("Project name", style=PROMPT_STYLE).unsafe_ask()

    return project_name, path_


def _prompt_port() -> int:
    port = text(
        "Port",
        default="5011",
        style=PROMPT_STYLE,
        validate=lambda port: port.isdigit()
        and (1024 <= int(port) <= 65535)
        or "Please enter a port number between 1024 and 65535",
    ).unsafe_ask()
    return int(port)


def _prompt_browser() -> str:
    return confirm("Auto-open browser", default=False, style=PROMPT_STYLE).unsafe_ask()


def _prompt_delete_entity() -> BaseModel:
    choices = [Choice(title=model.value.title(), value=model.value) for model in BaseModel]
    value = select(
        "Eentity to delete",
        choices=choices,
        style=PROMPT_STYLE,
        use_indicator=True,
        use_emacs_keys=True,
    ).unsafe_ask()
    return BaseModel(value)


def _prompt_delete_id(delete_entity: BaseModel) -> int:
    value = text(
        f"Database id of the {delete_entity.title()} you want to delete",
        style=PROMPT_STYLE,
        validate=lambda text: text.isdigit() or "Please enter a valid integer database id",
    ).unsafe_ask()
    return int(value)


def _prompt_status_level() -> StatusLevel:
    choices = [Choice(title=level.description, value=level.value) for level in StatusLevel]
    value = select(
        "Status Level",
        choices=choices,
        default=choices[0],
        style=PROMPT_STYLE,
        use_indicator=True,
        use_emacs_keys=True,
    ).unsafe_ask()
    return StatusLevel(value)


def _prompt_report_level() -> ReportLevel:
    choices = [Choice(title=level.description, value=level.value) for level in ReportLevel]
    value = select(
        "Report detail level",
        choices=choices,
        style=PROMPT_STYLE,
        default=ReportLevel.SUMMARY,
        use_indicator=True,
        use_emacs_keys=True,
    ).unsafe_ask()
    return ReportLevel(value)


def _prompt_tool_analysis(args: Namespace, message: str) -> str:
    state = load_state()
    kwargs = dict()
    if last_tool_analysis := state.get("last_tool_analysis"):
        kwargs["default"] = last_tool_analysis

    choices = [Choice(title="-ALL-", value="")]
    for o_tool in args.tools.values():
        # Each tool goes out "as itself":
        if len(o_tool.analyses) == 1:
            # Tool only has 1 analysis..
            title = o_tool.analyses[o_tool.name]
        else:
            # Tool only has multiple analyses, thus, the option here is to run ALL of them!
            title = f"{o_tool.name.title()} - ALL"
        choice = Choice(title=title, value=o_tool.name)
        choices.append(choice)

        # For tools with multiple analyses, put another option out for each one..
        if len(o_tool.analyses) > 1:
            for analysis, description in o_tool.analyses.items():
                value = f"{o_tool.name}:{analysis}"
                title = f"{o_tool.name.title()} - {description}"
                choice = Choice(title, value=value)
                choices.append(choice)

    return select(message=message, choices=choices, style=PROMPT_STYLE, **kwargs).unsafe_ask()
