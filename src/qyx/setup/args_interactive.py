"""."""

import sys
from argparse import Namespace

from questionary import Separator, Style, Choice, confirm, path, select, text
from questionary import print as qprint

from qyx.constants import BaseModel
from qyx.constants import ReportLevel as Rl
from qyx.constants import StatusLevel
from qyx.tools.base import Project, Request, Scan, State
from qyx.utils import dt_to_display

# fmt: off
PROMPT_STYLE = Style([
    # These seem to be the only ones worth spending time on (there are a lot more though)
    ('highlighted' , 'bold'),
    ('qmark'       , 'fg:#5f87af bold'),
    ('separator'   , 'fg:#cccccc'),
    ('question'    , 'fg:#5f87af bold'),
])
# fmt: on


def get_args_interactively(args: Namespace, iter: int) -> Namespace:
    if not iter:
        # Only print title the first time through...
        qprint("QYX → Code Quality Analysis Tool", style="bold italic")  #  fg:darkblue")

    try:
        args.command = _select_main_command(args)
        args = _get_command_args(args)
    except KeyboardInterrupt:
        _goodbye()

    qprint("")  # Add an extra line to demarcate whatever comes below...
    return args


def _get_command_args(args: Namespace) -> Namespace:
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
        case "_exit_":
            _goodbye()
    return args


def _goodbye():
    qprint(
        "Thanks, gracias, merci, danka, ありがとう, cпacи6o, köszönöm...!",
        style="bold italic fg:green",
    )
    sys.exit(0)


def _lookup_state_default(key: str) -> dict | None:
    """Return the default kwargs entry based on current state for the respective key."""
    kwargs = {}
    last_command = State.lookup(key)
    if last_command:
        kwargs["default"] = last_command
    return kwargs


def _select_main_command(args: Namespace):
    """Prompt user for primary command to run."""
    # fmt: off
    choices = [
        Choice(title="Status", value="status" , shortcut_key="s"),
        Choice(title="Report", value="report" , shortcut_key="r"),
        Choice(title="Ingest", value="ingest" , shortcut_key="i"),
        Choice(title="Serve" , value="serve"  , shortcut_key="v"),
        Choice(title="Admin" , value="admin"  , shortcut_key="a"),
        Separator("────────────"),
        Choice(title="Exit"  , value="_exit_" , shortcut_key="x"), # SENTINEL!
    ]
    # fmt: on

    kwargs = _lookup_state_default("command")
    command = select(
        "Command:",
        choices=choices,
        style=PROMPT_STYLE,
        use_indicator=True,
        use_shortcuts=True,
        **kwargs,
    ).unsafe_ask()

    if command != "_exit_":
        State.update(args, command=command)

    return command


################################################################################################
def _prompt_command_status(args: Namespace) -> Namespace:
    args.name = _prompt_name(args)
    args.level = _prompt_status_level()
    return args


def _prompt_command_report(args: Namespace) -> Namespace:
    args.name = _prompt_name(args)
    args.analysis = _prompt_analysis(args, "Analysis:")
    args.level = _prompt_report_level()
    return args


def _prompt_command_ingest(args: Namespace) -> Namespace:
    args.name = _prompt_name(args, include_new_option=True)
    args.path = _prompt_path(args)
    args.analysis = _prompt_analysis(args, "Analysis:")
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
            title="Delete a scan, request or project",
            value="delete",
            shortcut_key="d",
        ),
        Choice(
            title="Run db housekeeping (clean fluff & vacuum data store)",
            value="clean",
            shortcut_key="c",
        ),
    ]

    args.admin_command = select(
        "Administration command:",
        choices=choices,
        style=PROMPT_STYLE,
        use_indicator=True,
        use_shortcuts=True,
    ).unsafe_ask()

    match args.admin_command:
        case "delete":
            args = _prompt_admin_command_delete(args)
        case "clean":
            pass  # No arguments required here!
    return args


def _prompt_admin_command_delete(args: Namespace) -> Namespace:
    delete_entity: BaseModel = _prompt_delete_entity()
    match delete_entity:
        case BaseModel.PROJECT:
            delete_id: int = _prompt_delete_project()
        case BaseModel.REQUEST:
            delete_id: int = _prompt_delete_request()
        case BaseModel.SCAN:
            delete_id: int = _prompt_delete_scan()
        case _:
            raise RuntimeError(f"Invalid delete_entity recieved!: {delete_entity}")
    args.delete_target: str = f"{delete_entity.value}:{delete_id}"
    args.no_confirm: bool = False  # Let the delete commmand itself do the confirmation.
    return args


################################################################################################
def _prompt_name(args: Namespace, include_new_option: bool = False):
    last_project = State.lookup("name")  # Get the name of the last project we've referred to..
    choices = []
    kwargs = dict()
    for project in Project.select().order_by(Project.name):
        if last_project and project.name.lower() == last_project.lower():
            kwargs["default"] = project.name
        choices.append(Choice(title=project.name))

    if include_new_option:
        choices.append(Choice(title="─── Add New ───", value="__new__"))  # SENTINEL!
    else:
        choices.append(Choice(title="─── All ───", value="*"))  # SENTINEL!

    name = select(
        "Project:",
        choices=choices,
        style=PROMPT_STYLE,
        use_indicator=True,
        **kwargs,
    ).unsafe_ask()

    if name == "__new__":  # SENTINEL!
        name = text("Project name:", style=PROMPT_STYLE).unsafe_ask()

    State.update(args, name=name)

    return name


def _prompt_path(args: Namespace) -> tuple[str, str]:
    """Prompt for appropriate path to ingest from (only used in this case)."""
    # See if we have any previous info on the project.
    try:
        project = Project.get(Project.name == args.name)
        # Have a project, find the history of request sources:
        arg_raws = {request.arg_raw for request in Request.select().where(Request.project == project)}
        arg_raws = list(arg_raws)
    except Project.DoesNotExist:
        arg_raws = []

    choices = [Choice(title=arg_raw, value=arg_raw) for arg_raw in arg_raws]
    choices.append(Choice(title="─── From new path ───", value="__path__"))  # SENTINEL (local to method only)
    choices.append(Choice(title="─── From new repo ───", value="__repo__"))  # SENTINEL (local to method only)

    source = select(
        "Source:",
        choices=choices,
        style=PROMPT_STYLE,
        use_indicator=True,
    ).unsafe_ask()

    if not source.startswith("__"):
        return source

    match source:
        case "__path__":
            path_ = path("Path:", style=PROMPT_STYLE, only_directories=True).unsafe_ask()
        case "__repo__":
            path_ = text("Git repo URL:", style=PROMPT_STYLE).unsafe_ask()

    return path_


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
        "Model:",
        choices=choices,
        style=PROMPT_STYLE,
        use_indicator=True,
    ).unsafe_ask()
    return BaseModel(value)


def _prompt_delete_project() -> int:
    choices = __get_project_choices()
    value = select(
        "Project to delete:",
        choices=choices,
        style=PROMPT_STYLE,
        use_indicator=True,
    ).unsafe_ask()
    return int(value)


def _prompt_delete_request() -> int:
    # First, get the project...
    choices = __get_project_choices()
    s_project_id = select(
        "Project to delete from:",
        choices=choices,
        style=PROMPT_STYLE,
        use_indicator=True,
    ).unsafe_ask()

    # Now, get the request to delete from this project:
    choices = []
    project = Project.get(Project.id == int(s_project_id))
    for request in Request.select().where(Request.project == project):
        most_current_scan = Scan.select(Scan.as_of).where(Scan.request == request).order_by(Scan.as_of).first()
        source = request.arg_normalised if request.is_git else request.arg_raw
        title = f"{dt_to_display(most_current_scan.as_of)} from {source}"
        choices.append(Choice(title=title, value=request.id))

    value = select(
        "Request to delete:",
        choices=choices,
        style=PROMPT_STYLE,
        use_indicator=True,
    ).unsafe_ask()

    return int(value)


def _prompt_delete_scan() -> int:
    # First, get the project...
    choices = __get_project_choices()
    s_project_id = select(
        "Project to delete from:",
        choices=choices,
        style=PROMPT_STYLE,
        use_indicator=True,
    ).unsafe_ask()

    # Secondly, get the request:
    choices = []
    project = Project.get(Project.id == int(s_project_id))
    for request in Request.select().where(Request.project == project):
        most_current_scan = Scan.select(Scan.as_of).where(Scan.request == request).order_by(Scan.as_of).first()
        source = request.arg_normalised if request.is_git else request.arg_raw
        title = f"{dt_to_display(most_current_scan.as_of)} from {source}"
        choices.append(Choice(title=title, value=request.id))

    s_request_id = select(
        "Request to delete from:",
        choices=choices,
        style=PROMPT_STYLE,
        use_indicator=True,
    ).unsafe_ask()

    # Finally, get the particular scan
    choices = []
    request = Request.get(Request.id == int(s_request_id))
    for scan in Scan.select().where(Scan.request == request):
        title = f"{scan.analysis_display()} as of {dt_to_display(scan.as_of)}"
        choices.append(Choice(title=title, value=scan.id))

    value = select(
        "Scan to delete:",
        choices=choices,
        style=PROMPT_STYLE,
        use_indicator=True,
    ).unsafe_ask()

    return int(value)


def _prompt_status_level() -> StatusLevel:
    choices = [Choice(title=level.description, value=level.value) for level in StatusLevel]
    value = select(
        "Status Level:",
        choices=choices,
        default=choices[0],
        style=PROMPT_STYLE,
        use_indicator=True,
    ).unsafe_ask()
    return StatusLevel(value)


def _prompt_report_level() -> Rl:
    choices = [Choice(title=level.description, value=level.value, shortcut_key=level.value) for level in Rl]
    # FIXME: Make the following work! (doesn't now as sentinel isn't in the Enum)
    # choices.append(Choice(title="─── All ───", value="*", shortcut_key="a"))  # SENTINEL!
    value = select(
        "Report Level:",
        choices=choices,
        style=PROMPT_STYLE,
        default=Rl.SUMMARY,
        use_indicator=True,
        use_shortcuts=True,
    ).unsafe_ask()
    return Rl(value)


def _prompt_analysis(args: Namespace, message: str) -> str:
    choices = []
    names = [o_tool.name for o_tool in args.tools.values()]
    for tool in sorted(names):
        o_tool = args.tools[tool]
        # Tools with a single analysis go out with just their analysis
        if len(o_tool.analyses) == 1:
            title = f"{o_tool.name:5s} - {o_tool.analyses[o_tool.name]}"
            choices.append(Choice(title=title, value=o_tool.name))

        else:
            # For tools with multiple analyses, put an option out for each analysis and and "all" one
            for analysis, description in o_tool.analyses.items():
                title = f"{o_tool.name:5s} - {description}"
                choices.append(Choice(title, value=analysis))
            choices.append(Choice(title=f"{o_tool.name} - ALL", value=o_tool.name))

    # Final choice is a "global" all
    choices.append(Choice(title="─── All ───", value="*"))  # SENTINEL!

    # Do we have an existing value to default?
    kwargs = _lookup_state_default("analysis")

    analysis = select(
        message=message,
        choices=choices,
        style=PROMPT_STYLE,
        **kwargs,
    ).unsafe_ask()

    State.update(args, analysis=analysis)

    return analysis


def __get_project_choices() -> list[Choice]:
    """Return the list of existing projects as choices (syntactic sugar)."""
    return [Choice(title=project.name, value=project.id) for project in Project.select().order_by(Project.name)]
