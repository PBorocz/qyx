"""Report data obo running 'cloc' tool."""

from fasthtml import common as fh

from mq.tools.base import Project, Scan
from mq.tools.cloc.report_web_renderers.cloc_0 import cloc_0
from mq.tools.cloc.report_web_renderers.cloc_1 import cloc_1
from mq.tools.cloc.report_web_renderers.cloc_2 import cloc_2
from mq.tools.cloc.report_web_renderers.cloc_h import cloc_h
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
        *render_project_selector(request, "/partials/new_project/cloc"),
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
    scan = Scan.get_most_recent(project, "cloc", "cloc")

    return fh.Section(
        fh.H1("Current Status ", fh.Small(f"As Of {scan.as_of_display(collapse_today=True)}")),
        fh.Details(fh.Summary("Summary"), name="details", open=True, *cloc_0(scan)),
        fh.Details(fh.Summary("By Directory"), name="details", *cloc_1(scan)),
        fh.Details(fh.Summary("By File"), name="details", *cloc_2(scan)),
        cls="bordered",
    )


################################################################################################
# History
################################################################################################
def render_history(request, s_project_id: str = None, analysis: str = None):
    if not s_project_id:
        return fh.Section()
    project = Project.get(Project.id == int(s_project_id))
    chart = cloc_h(request.app.state.args, project)
    return fh.Section(
        fh.H1("History", style="margin-top: 1rem;"),
        fh.Div(
            fh.NotStr(chart.decode("utf-8")),
            cls="bordered",
        ),
    )
