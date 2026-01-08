"""Report data obo running 'fxtd' tool/script."""

from argparse import Namespace
from datetime import datetime

from pygal import DateTimeLine
from pygal.style import Style
from fasthtml import common as fh

from mq.tools.base import Project, Scan

from mq.tools.fxtd.models import query
from mq.tools.fxtd.report_web_renderers.fxtd_0 import fxtd_0
from mq.tools.fxtd.report_web_renderers.fxtd_1 import fxtd_1
from mq.tools.fxtd.report_web_renderers.fxtd_2 import fxtd_2
from mq.tools.fxtd.report_web_renderers.fxtd_h import fxtd_h
from mq.web.page import render_page


################################################################################################
# Page layout...
################################################################################################
def render(request, name, config):
    """Do the primary page layout for this tools display page."""
    return render_page(
        request,
        name,
        name.title(),
        *render_project_selector(request),
        # This Div will be updated as the project changes via HTMX!
        fh.Div(id="project-content"),
    )


################################################################################################
# Project Selector
################################################################################################
# FIXME: This is VERY COMMON across all tools, refactor to make it so!
def render_project_selector(request):
    projects = Project.select().order_by(Project.name)
    if not projects:
        return None

    # Convert our project(s) into selector items..
    elif len(projects) > 1:
        fh_select_items = [fh.Option("Project...", value="")]
        for project in projects:
            fh_select_items.append(fh.Option(project.name, value=str(project.id)))

    elif len(projects) == 1:
        project = projects[0]
        fh_select_items = [fh.Option(project.name, value=str(project.id), selected=True)]

    # And return our selector form
    return fh.Form(
        fh.Fieldset(
            fh.Select(
                *fh_select_items,
                name="project",
                aria_label="Select your project...",
                hx_get="/partials/fxtd_set_project",  # HTMX endpoint
                hx_target="#project-content",  # Where to update
                hx_swap="innerHTML",  # How to update
                hx_trigger="load, change",  # Trigger on page load *AND* selection change
            ),
        ),
    )


################################################################################################
# Current Status at 3 Levels
################################################################################################
def render_accordion_levels(request, s_project_id: str = None):
    if not s_project_id:
        return fh.Section()
    args = request.app.state.args
    project = Project.get(Project.id == int(s_project_id))
    scan = Scan.get_most_recent(project, "fxtd", "fxtd")

    return fh.Section(
        fh.H1("Current Status ", fh.Small(f"As Of {scan.as_of_display(collapse_today=True)}")),
        fh.Details(fh.Summary("Summary"), name="details", open=True, *fxtd_0(args, scan)),
        fh.Details(fh.Summary("By Directory"), name="details", *fxtd_1(args, scan)),
        fh.Details(fh.Summary("By File"), name="details", *fxtd_2(args, scan)),
        cls="bordered",
    )


################################################################################################
# History
################################################################################################
def render_history_chart(request, s_project_id: str = None):
    # Create Pygal chart
    if not s_project_id:
        return fh.Section()
    project = Project.get(Project.id == int(s_project_id))
    chart = fxtd_h(request.app.state.args, project)
    return fh.Section(
        fh.H1("History", style="margin-top: 1rem;"),
        fh.Div(fh.NotStr(chart.decode("utf-8")), cls="bordered"),
    )
