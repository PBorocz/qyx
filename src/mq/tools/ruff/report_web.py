"""Report data obo running 'ruff' tool."""

from fasthtml import common as fh

from mq.tools.base import Project, Scan

from mq.web import render_project_selector
from mq.web.page import render_page
from mq.tools.ruff.report_web_renderers.ruff_0 import ruff_0
from mq.tools.ruff.report_web_renderers.ruff_1 import ruff_1
from mq.tools.ruff.report_web_renderers.ruff_2 import ruff_2
from mq.tools.ruff.report_web_renderers.ruff_h import ruff_h


################################################################################################
# Page layout...
################################################################################################
def render(request, name, config):
    """Do the primary page layout for this tools display page."""
    return render_page(
        request,
        name.title(),
        name,
        *render_project_selector(request, "/partials/new_project/ruff"),
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
    scan = Scan.get_most_recent(project, "ruff", "ruff")

    return fh.Section(
        fh.H1("Current Status ", fh.Small(f"As Of {scan.as_of_display(collapse_today=True)}")),
        fh.Details(fh.Summary("Summary"), name="details", open=True, *ruff_0(args, scan)),
        fh.Details(fh.Summary("By Rule"), name="details", open=False, *ruff_1(args, scan)),
        fh.Details(fh.Summary("By File"), name="details", open=False, *ruff_2(args, scan)),
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
    chart = ruff_h(request.app.state.args, project)
    return fh.Section(
        fh.H1("History", style="margin-top: 1rem;"),
        fh.Div(fh.NotStr(chart.decode("utf-8")), cls="bordered"),
    )
