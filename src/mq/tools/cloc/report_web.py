"""Report data obo running 'cloc' tool."""

from argparse import Namespace
from fasthtml import common as fh

from mq.tools.base import Project, Scan
from mq.tools.cloc.report_web_renderers.cloc_0 import cloc_0
from mq.tools.cloc.report_web_renderers.cloc_1 import cloc_1
from mq.tools.cloc.report_web_renderers.cloc_2 import cloc_2
from mq.tools.cloc.report_web_renderers.cloc_d import cloc_d
from mq.tools.cloc.report_web_renderers.cloc_h import cloc_h
from mq.tools.cloc.report_web_renderers.cloc_f import cloc_f
from mq.web import render_project_selector
from mq.web.page import render_page


# Page layout...
def render(request, name, config):
    """Do the primary page layout for this tools display page."""
    return render_page(
        request,
        name.title(),
        name,
        *render_project_selector(request, "/partials/set_project/cloc"),
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
    """Render the current status."""
    if not s_project_id:
        return fh.Section()
    project = Project.get(Project.id == int(s_project_id))
    scan = Scan.get_most_recent(project, "cloc", "cloc")

    chart_file_sizes = cloc_f(scan)

    return fh.Section(
        fh.H1("Current Status ", fh.Small(f"As Of {scan.as_of_display(collapse_today=True)}")),
        fh.Details(fh.Summary("Summary"), name="details", open=True, *cloc_0(scan)),
        fh.Details(fh.Summary("By Directory"), name="details", *cloc_1(scan)),
        fh.Details(fh.Summary("By File"), name="details", *cloc_2(scan)),
        fh.Details(fh.Summary("Derived"), name="details", *cloc_d(project, scan)),
        fh.Details(
            fh.Summary("File Sizes"),
            fh.Section(fh.Div(fh.NotStr(chart_file_sizes.decode("utf-8"))), cls="bordered"),
            name="details",
        ),
        cls="bordered",
    )


def _render_history(args: Namespace, request, s_project_id: str = None, analysis: str = None):
    """Render any history."""
    if not s_project_id:
        return fh.Section()
    project = Project.get(Project.id == int(s_project_id))
    chart = cloc_h(project)

    return fh.Section(
        fh.H1("History", style="margin-top: 1rem;"),
        fh.Div(
            fh.NotStr(chart.decode("utf-8")),
            cls="bordered",
        ),
    )
