"""Core page rendering methods, full (Bottle) and partial (HTMX)."""

import logging
from types import SimpleNamespace as Sns
from typing import Callable

from bottle import request

from qyx.tools.base import Project
from qyx.web import get_project_selector, get_scan_selector


log = logging.getLogger(__name__)


def generic_render(tool_name: str, template: str, content_method: Callable) -> str:
    """Render the primary page layout for this tools display page."""
    project_options, project = get_project_selector(tool_name)
    if not project:
        log.error("Sorry, no projects yet?")
        return render_partial("base::_no_projects_yet.htmx")

    scan_options, scan = get_scan_selector(project, tool_name)
    if not scan:
        log.error(f"Sorry, no scans yet for {project.name=}?")
        return render_partial("base::_no_scans_yet.htmx")

    context: Sns = content_method(scan)  # Get the "body" content as an Sns context..
    context.project_options = project_options
    context.scan_options = scan_options
    context.hx_get_scans = f"/{tool_name}/scans"
    context.hx_get_content = f"/{tool_name}/content"

    title = f"QYX-{tool_name.upper()}"
    return render_page(title, template, **context.__dict__)


def generic_render_scans(tool_name: str, template: str = "base::_select_scan.cascading.html") -> str:
    """Render the specified tool's scan select widget based on a new project selection."""
    s_project_id = request.query.project
    project = Project.get_or_none(Project.id == int(s_project_id)) if s_project_id else None

    scan_options, scan = get_scan_selector(project, tool_name)
    return render_partial(template, scan_options=scan_options, hx_get_content=f"/{tool_name}/content")


def render_page(title: str, template: str, **context) -> str:
    """Render the specified *FULL* page template using the context provided."""
    context["title"] = title
    context["navbar"] = [
        {"name": tool_name, "description": tool_name.title()}
        for tool_name in request.app.args.config.get("renderers.web.ui.tool_order")
    ]
    return _render_template(template, **context)


def render_partial(template: str, **context) -> str:
    """Render the specified *PARTIAL* page template (usually a .htmx one) using the context provided."""
    return _render_template(template, **context)


def _render_template(template: str, **context) -> str:
    """Lowest level, render the template provided using the context provided."""
    context["current_path"] = request.path  # Pass back for Navbar management.
    return request.app.args.jinja_env.get_template(template).render(**context)
