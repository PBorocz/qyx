"""Report data obo running 'fxtd' tool/script."""

from argparse import Namespace

from fasthtml import common as fh

from mq.tools.base import Project, Scan
from mq.tools.fxtd.report.web.fxtd_0 import fxtd_0
from mq.tools.fxtd.report.web.fxtd_1 import fxtd_1
from mq.tools.fxtd.report.web.fxtd_2 import fxtd_2
from mq.tools.fxtd.report.web.fxtd_h import fxtd_h
from mq.web import render_project_selector
from mq.web.page import render_page


################################################################################################
# Page layout...
################################################################################################
def render(request, name, config):
    """Do the primary page layout for this tools display page."""
    return render_page(
        request,
        name.title(),
        name,
        *render_project_selector(request, "/partials/set_project/fxtd"),
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
    scan = Scan.get_most_recent(project, "fxtd", "fxtd")

    return fh.Section(
        fh.H1("Current Status ", fh.Small(f"As Of {scan.as_of_display(collapse_today=True)}")),
        fh.Details(fh.Summary("Summary"), name="details", open=True, *fxtd_0(scan)),
        fh.Details(fh.Summary("By Directory"), name="details", *fxtd_1(scan)),
        fh.Details(fh.Summary("By File"), name="details", *fxtd_2(scan)),
        cls="bordered",
    )


def _render_history(args: Namespace, request, s_project_id: str = None, analysis: str = None):
    """Render the history portion of the page."""
    # Create Pygal chart
    if not s_project_id:
        return fh.Section()
    project = Project.get(Project.id == int(s_project_id))
    chart = fxtd_h(project)
    return fh.Section(
        fh.H1("History", style="margin-top: 1rem;"),
        fh.Div(fh.NotStr(chart.decode("utf-8")), cls="bordered"),
    )
