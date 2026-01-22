"""Report data obo running 'ruff' tool."""

from argparse import Namespace
from fasthtml import common as fh

from mq.tools.base import Project, Scan

from mq.web import render_project_selector
from mq.web.page import render_page
from mq.tools.ruff.report.web.ruff_0 import ruff_0
from mq.tools.ruff.report.web.ruff_1 import ruff_1
from mq.tools.ruff.report.web.ruff_2 import ruff_2
from mq.tools.ruff.report.web.ruff_h import ruff_h


################################################################################################
# Page layout...
################################################################################################
def render(request, name, config):
    """Do the primary page layout for this tools display page."""
    return render_page(
        request,
        name.title(),
        name,
        *render_project_selector(request, "/partials/set_project/ruff"),
        fh.Div(id="page-body-content"),
    )


################################################################################################
def render_content(args: Namespace, request, s_project_id: str = None, analysis: str = None):
    """Render the content portion (ie. body) of the page."""
    return (
        *_render_current(args, request, s_project_id, analysis),
        *_render_history(args, request, s_project_id, analysis),
    )


def _render_current(args: Namespace, request, s_project_id: str = None, analysis: str = None):
    """Render the current status portion of the page."""
    if not s_project_id:
        return fh.Section()
    project = Project.get(Project.id == int(s_project_id))
    scan = Scan.get_most_recent(project, "ruff", "ruff")

    return fh.Section(
        fh.H1("Current Status ", fh.Small(f"As Of {scan.as_of_display(collapse_today=True)}")),
        fh.Details(fh.Summary("Summary"), name="details", open=True, *ruff_0(scan)),
        fh.Details(fh.Summary("By Rule"), name="details", open=False, *ruff_1(scan)),
        fh.Details(fh.Summary("By File"), name="details", open=False, *ruff_2(scan)),
        cls="bordered",
    )


def _render_history(args: Namespace, request, s_project_id: str = None, analysis: str = None):
    """Render the history portion of the page."""
    # Create Pygal chart
    if not s_project_id:
        return fh.Section()
    project = Project.get(Project.id == int(s_project_id))
    chart = ruff_h(project)
    return fh.Section(
        fh.H1("History", style="margin-top: 1rem;"),
        fh.Div(fh.NotStr(chart.decode("utf-8")), cls="bordered"),
    )
