"""Render the "home"/summary page."""

from argparse import Namespace

from fasthtml import common as fh

from mq.tools.base import Project, Scan
from mq.tools.cloc.report_web_renderers.cloc_0 import cloc_0
from mq.tools.cloc.report_web_renderers.cloc_d import cloc_d
from mq.tools.fxtd.report_web_renderers.fxtd_0 import fxtd_0
from mq.tools.fxtd.report_web_renderers.fxtd_d import fxtd_d
from mq.tools.radon.report_web_renderers.cc_0 import cc_0
from mq.tools.radon.report_web_renderers.cc_d import cc_d
from mq.tools.radon.report_web_renderers.hal_0 import hal_0
from mq.tools.radon.report_web_renderers.hal_d import hal_d
from mq.tools.radon.report_web_renderers.mi_0 import mi_0
from mq.tools.radon.report_web_renderers.mi_d import mi_d
from mq.tools.radon.report_web_renderers.raw_0 import raw_0
from mq.tools.ruff.report_web_renderers.ruff_0 import ruff_0
from mq.tools.ruff.report_web_renderers.ruff_d import ruff_d
from mq.web import render_project_selector
from mq.web.page import render_page


################################################################################################
# Page layout...
################################################################################################
def render_page_home(request):
    return render_page(
        request,
        None,
        None,
        fh.H1("Code Quality - Project Summary"),
        *render_project_selector(request, "/partials/new_project/_main_"),
        fh.Div(id="page-body-content"),
    )


def render_partial_project_summary(request, s_project_id: str):
    """Render the home/summary page."""
    if not s_project_id:
        return fh.Section()

    # Find the respective project to display results for
    project = Project.get(Project.id == int(s_project_id))

    # Query all level 0 summaries of raw results as well as derived metrics:
    args = request.app.state.args
    project_level_0s = get_project_level_0s(args, project)
    project_level_ds = get_project_level_ds(args, project)

    # Render our grid of results.
    fh_section = fh.Section(
        fh.Div(
            fh.Div(fh.H3("Raw Metrics")),
            fh.Div(fh.H3("Derived Metrics")),
            cls="grid",
        ),
        fh.Div(
            fh.Div(*project_level_0s.get(("cloc", "cloc"), [])),
            fh.Div(*project_level_ds.get(("cloc", "cloc"), [])),
            cls="grid",
        ),
        fh.Div(
            fh.Div(*project_level_0s.get(("ruff", "ruff"), [])),
            fh.Div(*project_level_ds.get(("ruff", "ruff"), [])),
            cls="grid",
        ),
        fh.Div(
            fh.Div(*project_level_0s.get(("fxtd", "fxtd"), [])),
            fh.Div(*project_level_ds.get(("fxtd", "fxtd"), [])),
            cls="grid",
        ),
        fh.Div(
            fh.Div(*project_level_0s.get(("radon", "mi"), [])),
            fh.Div(*project_level_ds.get(("radon", "mi"), [])),
            cls="grid",
        ),
        fh.Div(
            fh.Div(*project_level_0s.get(("radon", "cc"), [])),
            fh.Div(*project_level_ds.get(("radon", "cc"), [])),
            cls="grid",
        ),
        fh.Div(
            fh.Div(*project_level_0s.get(("radon", "hal"), [])),
            fh.Div(*project_level_ds.get(("radon", "hal"), [])),
            cls="grid",
        ),
        fh.Div(
            fh.Div(*project_level_0s.get(("radon", "raw"), [])),
            fh.Div(*project_level_ds.get(("radon", "raw"), [])),
            cls="grid",
        ),
    )
    return ((fh_section),)


def get_project_level_0s(args: Namespace, project: Project) -> dict:
    content = dict()

    # FIXME: Make this dynamic based on configuration and import_lib availability of the methods.
    for tool, analysis, level_method in (
        ("cloc", "cloc", cloc_0),
        ("ruff", "ruff", ruff_0),
        ("fxtd", "fxtd", fxtd_0),
        ("radon", "cc", cc_0),
        ("radon", "hal", hal_0),
        ("radon", "mi", mi_0),
        ("radon", "raw", raw_0),
    ):
        if scan := Scan.get_most_recent(project, tool, analysis):
            if level_contents := level_method(scan):
                content[(tool, analysis)] = level_contents

    return content


def get_project_level_ds(args: Namespace, project: Project) -> dict:
    content = dict()

    # FIXME: Make this dynamic based on configuration and import_lib availability of the methods.
    for tool, analysis, level_method in (
        ("cloc", "cloc", cloc_d),
        ("fxtd", "fxtd", fxtd_d),
        ("radon", "cc", cc_d),
        ("radon", "hal", hal_d),
        ("radon", "mi", mi_d),
        ("ruff", "ruff", ruff_d),
        # ("radon", "raw", raw_d),
    ):
        if scan := Scan.get_most_recent(project, tool, analysis):
            if level_contents := level_method(project=project, scan=scan):
                content[(tool, analysis)] = level_contents

    return content
