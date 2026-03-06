"""Core page rendering methods, full (Bottle) and partial (HTMX)."""

import logging
from dataclasses import dataclass
from types import SimpleNamespace as Sns
from typing import Callable

from bottle import request

from qyx.tools.base import Project, Request, Scan, State, ToolType


log = logging.getLogger(__name__)


################################################################################################
def render(tool: ToolType, template: str, content_method: Callable) -> str:
    """Render the primary page layout for this tools display page."""
    project_options, project = get_project_selector(tool)
    if not project:
        return render_template("base::_no_projects_yet.html")

    # (we may or may not use the analysis_options but it's inexpensive to create)
    analysis_options, analysis = get_analysis_selector(tool, project)
    if not analysis:
        return render_template("base::_no_scans_yet.html")

    scan = Scan.get_most_recent(project, tool.name, analysis)
    if not scan:
        return render_template("base::_no_scans_yet.html")

    context: Sns = content_method(scan)  # Get the "body" content as an Sns context..
    context.tool = tool.name
    context.analysis = analysis
    context.project_options = project_options

    if len(tool.analyses) == 1:
        # Single analysis case: Changing project goes immediately to populating the page
        context.hx_change_project_url = f"/{tool.name}/content"
        context.hx_change_project_target = "#div_body_content"
    else:
        # Multiple analysis case: Changing project goes instead to selecting relevant analysis..
        context.analysis_options = analysis_options
        context.hx_change_project_url = f"/{tool.name}/analysis"
        context.hx_change_project_target = "#div_select_analysis"

        # And updating the analysis populates the body of the page.
        context.hx_change_analysis_url = f"/{tool.name}/content"

    return render_page(f"QYX-{tool.name.upper()}", template, **context.__dict__)


################################################################################################
def render_content(project: str | Project, tool: ToolType, analysis: str, content_method: Callable) -> str:
    """Render the HTML associated with the body of the respective tool page."""
    # If we haven't done so, lookup the project..
    if isinstance(project, str):
        project: Project | None = Project.get(Project.id == int(project))
        if not project:
            return render_template("base::_no_scans_yet.html")

    # Find the most recent scan on behalf of this project...
    scan: Scan | None = Scan.get_most_recent(project, tool.name, analysis)
    if not scan:
        return render_template("base::_no_scans_yet.html")

    context: Sns = content_method(scan)
    template: str = f"{tool.name}::{analysis}.html"
    return render_template(template, **context.__dict__)


################################################################################################
def render_analyses(tool: ToolType, project: str, content_method: Callable) -> str:
    """Render BOTH the new analysis widget associated with the new project *AND* update content on an OOB basis."""
    # Find the currently selected project..
    project = Project.get_or_none(Project.id == int(project)) if project else None

    # Get the analysis options associated with this tool and scan's for the project.
    html_select_analysis_widget, analysis = _build_analysis_selector(tool, project)

    # Render the "body" portion given the new project *and* potentially a different analysis!
    html_div_body = render_content(project, tool, analysis, content_method)

    return f'{html_select_analysis_widget}<div id="div_body_content" hx-swap-oob="true">{html_div_body}</div>'


def _build_analysis_selector(tool: ToolType, project: Project) -> tuple[str, str]:
    # Get the analysis options associated with this tool and scan's for the project.
    analysis_options, analysis = get_analysis_selector(tool, project)

    # Render the HTML associated with the analysis select widget given the new project
    context = Sns(analysis_options=analysis_options, hx_change_analysis_url=f"/{tool.name}/content")
    template = "base::_select_analysis.html"
    return (render_template(template, **context.__dict__), analysis)


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
    """Return a selection widget over all projects that have every had a scan for the specified tool."""
    projects = Project.select().join(Request).join(Scan).distinct().order_by(Project.name)
    if tool:
        analyses = list(tool.analyses.keys())
        projects = projects.where(Scan.analysis.in_(analyses))

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


def get_analysis_selector(tool: ToolType, project: Project) -> tuple[list[Option] | str]:
    """Return a form to allow selection over all analyses for the specified tool and project."""
    query = (
        Scan.select(Scan.analysis)
        .join(Request)
        .where(Request.project == project)
        .where(Scan.tool == tool.name)
        .distinct()
        .order_by(
            Scan.analysis,
        )
    )
    analyses = []
    for scan_partial in query:
        if scan_partial.analysis in tool.analyses:
            analyses.append((scan_partial.analysis, tool.analyses[scan_partial.analysis]))

    last_analysis = State.lookup("analysis")

    selected_analysis = None
    if last_analysis:
        for analysis, _ in analyses:
            if last_analysis.lower() == project.name.lower():
                selected_analysis = analysis
                break

    # If no match found (or no last_analysis), default to first
    if selected_analysis is None:
        selected_analysis = analyses[0][0]

    # Build options now that we know which is the selected entry..
    options = []
    for value, display in analyses:
        selected = value == selected_analysis
        options.append(Option(value=value, display=display, selected=selected))

    return options, selected_analysis
