"""Render the "home"/summary page."""

from argparse import Namespace

from fasthtml import common as fh

from mq.tools.base import Project, Scan
from mq.tools.cloc.report_web_renderers.cloc_0 import cloc_0
from mq.tools.cloc.report_web_renderers.cloc_d import cloc_d
from mq.tools.fxtd.report_web_renderers.fxtd_0 import fxtd_0
from mq.tools.radon.report_web_renderers.cc_0 import cc_0
from mq.tools.radon.report_web_renderers.hal_0 import hal_0
from mq.tools.radon.report_web_renderers.mi_0 import mi_0
from mq.tools.radon.report_web_renderers.raw_0 import raw_0
from mq.tools.ruff.report_web_renderers.ruff_0 import ruff_0
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
    args = request.app.state.args
    project = Project.get(Project.id == int(s_project_id))
    project_level_0s = get_project_level_0s(args, project)
    project_level_ds = get_project_level_ds(args, project)

    page_contents = []

    fh_section = fh.Section(
        fh.Div(
            fh.Div(*project_level_0s[("cloc", "cloc")]),
            fh.Div(*project_level_ds[("cloc", "cloc")]),
            cls="grid",
        ),
        fh.Div(
            fh.Div(*project_level_0s[("ruff", "ruff")]),
            # fh.Div(*project_level_0s[("ruff", "ruff")]),
            cls="grid",
        ),
        fh.Div(
            fh.Div(*project_level_0s[("radon", "mi")]),
            # fh.Div(*project_level_0s[("radon", "mi")]),
            cls="grid",
        ),
        fh.Div(
            fh.Div(*project_level_0s[("radon", "cc")]),
            # fh.Div(*project_level_0s[("radon", "cc")]),
            cls="grid",
        ),
        fh.Div(
            fh.Div(*project_level_0s[("radon", "hal")]),
            # fh.Div(*project_level_0s[("radon", "hal")]),
            cls="grid",
        ),
        fh.Div(
            fh.Div(*project_level_0s[("radon", "raw")]),
            # fh.Div(*project_level_0s[("radon", "raw")]),
            cls="grid",
        ),
        fh.Div(
            fh.Div(*project_level_0s[("fxtd", "fxtd")]),
            # fh.Div(*project_level_0s[("fxtd", "fxtd")]),
            cls="grid",
        ),
    )
    page_contents.append(fh_section)

    return (*page_contents,)


def get_project_level_0s(args: Namespace, project: Project) -> dict:
    content = dict()

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
            if level_contents := level_method(args, scan):
                h3 = tool.title() if tool == analysis else f"{tool.title()}: {analysis.upper()}"
                content[(tool, analysis)] = (fh.H4(h3), *level_contents)

    return content


def get_project_level_ds(args: Namespace, project: Project) -> dict:
    content = dict()

    for tool, analysis, level_method in (
        ("cloc", "cloc", cloc_d),
        # ("ruff", "ruff", ruff_0),
        # ("fxtd", "fxtd", fxtd_0),
        # ("radon", "cc", cc_0),
        # ("radon", "hal", hal_0),
        # ("radon", "mi", mi_0),
        # ("radon", "raw", raw_0),
    ):
        if scan := Scan.get_most_recent(project, tool, analysis):
            if level_contents := level_method(args, scan):
                h3 = tool.title() if tool == analysis else f"{tool.title()}: {analysis.upper()}"
                content[(tool, analysis)] = (fh.H4(h3), *level_contents)

    return content
