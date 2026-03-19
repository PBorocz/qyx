"""Core page rendering methods, full (Bottle) and partial (HTMX)."""

import logging
from dataclasses import dataclass
from types import SimpleNamespace as Sns
from typing import Callable

from bottle import request

from qyx.tools._models_ import Project, Request, Scan, State, ToolDimension, ToolType


log = logging.getLogger(__name__)


################################################################################################
def render(tool: ToolType, template: str, content_method: Callable) -> str:
    """Render the primary page layout for this a tool's primary display page."""
    project_options, project = get_project_selector(tool)
    if not project:
        return render_template("base::_no_projects_yet.html")

    # (we may or may not use the dimension selector options but it's inexpensive to create)
    dimension_options, dimension = _get_dimension_selector(tool, project)
    if not dimension:
        return render_template("base::_no_scans_yet.html")
    log.debug(f"selected dimension: {dimension.__dict__=}")

    if tool.ingest_by_dimension:
        scan = Scan.get_latest(project, tool.name, dimension.cli_option)
        log.debug(f"ingest_by_dimension: {dimension.cli_option=}")
    else:
        scan = Scan.get_latest(project, tool.name)
        log.debug(f"ingest_by_tool_only: {tool.name=}")
    if not scan:
        return render_template("base::_no_scans_yet.html")

    context: Sns = content_method(scan, dimension.name)  # Callback into the tool to get the "body" content as an Sns
    context.tool = tool.name
    context.dimension = dimension
    context.project_options = project_options
    context.dimension_options = dimension_options

    if len(tool.dimensions) == 1:
        # Single dimension case: Changing project goes immediately to populating the page
        context.hx_change_project_url = f"/{tool.name}/content"
        context.hx_change_project_target = "#div_body_content"
    else:
        # Multiple dimension case: Changing project goes instead to selecting relevant dimension..
        context.hx_change_project_url = f"/{tool.name}/dimension"
        context.hx_change_project_target = "#div_select_dimension"

        # And updating the dimension populates the body of the page.
        context.hx_change_dimension_url = f"/{tool.name}/content"

    return render_page(f"QYX-{tool.name.upper()}", template, **context.__dict__)


################################################################################################
def render_content(project: str | Project, tool: ToolType, dimension: str | None, content_method: Callable) -> str:
    """Render the HTML associated with the body of the respective tool page."""
    # If we haven't done so, lookup the project..
    if isinstance(project, str):
        project: Project | None = Project.get(Project.id == int(project))
        if not project:
            return render_template("base::_no_scans_yet.html")

    # Find the most recent scan on behalf of this project...
    if tool.ingest_by_dimension:
        # Scan's are specific to the dimension, pick the one
        # associated with the requested dimension (e.g. "raw" for Radon).
        scan: Scan | None = Scan.get_latest(project, tool.name, dimension)
    else:
        # Irrespective of reporting dimensions, we ingest a single time for the tool, e.g. cloc, ruff,.. AND scc!
        scan: Scan | None = Scan.get_latest(project, tool.name)
    if not scan:
        return render_template("base::_no_scans_yet.html")

    ################################################################################
    # CORE! Run the "body" content method associated with the tool and reporting dimension!
    ################################################################################
    context: Sns = content_method(scan, dimension)

    try:
        template: str = f"{tool.name}::{dimension}.html"
        return render_template(template, **context.__dict__)
    except Exception:
        pass
    template: str = f"{tool.name}::{tool.name}.html"
    return render_template(template, **context.__dict__)


################################################################################################
def render_dimensions(tool: ToolType, s_project_id: str, content_method: Callable) -> str:
    """Render BOTH the new dimension widget associated with the new project *AND* update content on an OOB basis."""
    # Find the currently selected project..
    project: Project | None = Project.get_or_none(Project.id == int(s_project_id)) if s_project_id else None
    if not project:
        return ""

    # Get the dimension options associated with this tool and scan's for the project.
    html_select_dimension_widget, dimension = _build_dimension_selector(tool, project)
    log.debug(f"selected dimension: {dimension.__dict__=}")

    # Render the "body" portion given the new project *and* potentially a different dimension!
    html_div_body: str = render_content(project, tool, dimension, content_method)

    return f'{html_select_dimension_widget}<div id="div_body_content" hx-swap-oob="true">{html_div_body}</div>'


def _build_dimension_selector(tool: ToolType, project: Project) -> tuple[str, str]:
    # Get the dimensions options associated with this tool and scan's for the project.
    dimension_options, dimension = _get_dimension_selector(tool, project)

    # Render the HTML associated with the dimension select widget given the new project
    context: Sns = Sns(dimension_options=dimension_options, hx_change_dimension_url=f"/{tool.name}/content")
    template: str = "base::_select_dimension.html"
    return (render_template(template, **context.__dict__), dimension)


################################################################################################
def render_page(title: str, template: str, **context) -> str:
    """Render the specified *FULL* page template using the context provided."""
    context["title"] = title
    context["navbar"] = [
        {"name": tool_name, "description": tool_name.title()}
        for tool_name in request.app.args.config.get("renderers.web.nav.tool_order")
    ]
    context["current_path"] = request.path  # Pass back for Navbar management.
    return render_template(template, **context)


def render_template(template: str, **context) -> str:
    """Lowest level, render the template provided using the context provided."""
    # Note: can be called directly as well for returning "partials", ie. HTMX snippets.
    return request.app.args.jinja_env.get_template(template).render(**context)


################################################################################################
# Utilities..
################################################################################################
@dataclass(frozen=True)
class Option:
    """Represents an option to be rendered into a select widget."""

    value: str
    display: str
    selected: bool = False


def get_project_selector(tool: ToolType | None = None) -> tuple[list[Option], Project | None]:
    """Return a selection widget over all projects that have every had a scan (or for the specified tool)."""
    projects = Project.select().join(Request).join(Scan).distinct().order_by(Project.name)
    if tool:
        projects = projects.where(Scan.tool == tool.name)

    ################################################################################
    # Case 1: No projects found! (very unusual case)
    ################################################################################
    if len(projects) == 0:
        return ([], None)

    ################################################################################
    # Case 2: Just a single project available.
    ################################################################################
    if len(projects) == 1:
        project = projects[0]
        options = [Option(value=str(project.id), display=project.name, selected=True)]
        return options, project

    ################################################################################
    # Case 3: Multiple projects case...
    ################################################################################
    options = [Option(display="Project...", value="")]
    last_project = State.lookup("project")

    # First pass: lookup the last_project (also to handle the case if it's disappeared!)
    selected_project = None
    if last_project:
        for project in projects:
            if last_project.lower() == project.name.lower():
                selected_project = project
                break

    # If no match found (or no last_project), default to first
    if selected_project is None:
        selected_project = projects[0]

    # Build options with correct selection
    for project in projects:
        selected = project == selected_project
        options.append(Option(value=str(project.id), display=project.name, selected=selected))

    return options, selected_project


def _get_dimension_selector(tool: ToolType, project: Project) -> tuple[list[Option], ToolDimension]:
    """Return a form to allow selection over all *REPORTING* dimensions for the specified tool and project."""
    if tool.ingest_by_dimension:
        # Eg. Radon and it's ilk:
        query = (
            Scan.select(Scan.ingest_dimension)
            .join(Request)
            .where(Request.project == project)
            .where(Scan.tool == tool.name)
            .distinct()
            .order_by(Scan.ingest_dimension)
        )
        dimensions = []
        for scan in query:
            if dimension := tool.find_dimension(scan.ingest_dimension):
                dimensions.append(dimension)
        log.debug(f"Found {len(dimensions)=}")
    else:
        # Single ingest and single or multiple reporting dimensions!
        dimensions = tool.dimensions

    last_dimension: str = State.lookup("dimension")

    selected_dimension: ToolDimension = None
    if last_dimension:
        for dimension in dimensions:
            if last_dimension.lower() == dimension.name.lower():
                selected_dimension = dimension
                break

    # If no match found (or no last_dimension), default to first
    if selected_dimension is None:
        selected_dimension = dimensions[0]

    # Build options now that we know which is the selected entry..
    options = []
    for dimension in dimensions:
        selected = dimension == selected_dimension
        options.append(Option(value=dimension.name, display=dimension.description, selected=selected))

    log.debug(f"{options=} {selected_dimension=}")
    return options, selected_dimension
