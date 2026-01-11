"""Report data obo running 'fxtd' tool/script."""

from fasthtml import common as fh

from mq.tools.base import Project, Scan
from mq.tools.fxtd.report_web_renderers.fxtd_0 import fxtd_0
from mq.tools.fxtd.report_web_renderers.fxtd_1 import fxtd_1
from mq.tools.fxtd.report_web_renderers.fxtd_2 import fxtd_2
from mq.tools.fxtd.report_web_renderers.fxtd_h import fxtd_h
from mq.web import render_project_selector
from mq.web.page import render_page


################################################################################################
# Page layout...
################################################################################################
def render(request, name, config, session):
    """Do the primary page layout for this tools display page."""
    return render_page(
        request,
        name.title(),
        name,
        session,
        *render_project_selector(request, session, "/partials/new_project/fxtd"),
        fh.Div(id="page-body-content"),
    )


################################################################################################
# Current Status
################################################################################################
def render_current(request, s_project_id: str = None, analysis: str = None):
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
def render_history(request, s_project_id: str = None, analysis: str = None):
    # Create Pygal chart
    if not s_project_id:
        return fh.Section()
    project = Project.get(Project.id == int(s_project_id))
    chart = fxtd_h(request.app.state.args, project)
    return fh.Section(
        fh.H1("History", style="margin-top: 1rem;"),
        fh.Div(fh.NotStr(chart.decode("utf-8")), cls="bordered"),
    )
