"""Render the "home"/summary page."""

import logging
from argparse import Namespace
from types import ModuleType
from typing import Callable, Iterator

from fasthtml import common as fh

from mq.tools.base import Project, Scan
from mq.web import render_project_selector
from mq.web.page import render_page


log = logging.getLogger(__name__)


################################################################################################
# Page layout...
################################################################################################
def render_page_home(request):
    return render_page(
        request,
        None,
        None,
        fh.H1("Code Quality - Project Summary"),
        *render_project_selector(request, "/partials/set_project/_main_"),
        fh.Div(id="page-body-content"),
    )


def render_partial_project_summary(request, s_project_id: str):
    """Render the home/summary page."""
    if not s_project_id:
        return fh.Section()

    # Find the respective project to display results for
    project = Project.get(Project.id == int(s_project_id))

    # Query all level 0 summaries of raw results as well as derived metrics:
    content = get_project_content(request.app.state.args, project)

    # Render our grid of results.
    fh_section = fh.Section(
        fh.Div(
            fh.Div(fh.H3("Raw Metrics")),
            fh.Div(fh.H3("Derived Metrics")),
            cls="grid",
        ),
        fh.Div(
            fh.Div(*content.get(("0", "cloc", "cloc"), [])),
            fh.Div(*content.get(("d", "cloc", "cloc"), [])),
            cls="grid",
        ),
        fh.Div(
            fh.Div(*content.get(("0", "ruff", "ruff"), [])),
            fh.Div(*content.get(("d", "ruff", "ruff"), [])),
            cls="grid",
        ),
        fh.Div(
            fh.Div(*content.get(("0", "fxtd", "fxtd"), [])),
            fh.Div(*content.get(("d", "fxtd", "fxtd"), [])),
            cls="grid",
        ),
        fh.Div(
            fh.Div(*content.get(("0", "radon", "mi"), [])),
            fh.Div(*content.get(("d", "radon", "mi"), [])),
            cls="grid",
        ),
        fh.Div(
            fh.Div(*content.get(("0", "radon", "cc"), [])),
            fh.Div(*content.get(("d", "radon", "cc"), [])),
            cls="grid",
        ),
        fh.Div(
            fh.Div(*content.get(("0", "radon", "hal"), [])),
            fh.Div(*content.get(("d", "radon", "hal"), [])),
            cls="grid",
        ),
        fh.Div(
            fh.Div(*content.get(("0", "radon", "raw"), [])),
            fh.Div(*content.get(("d", "radon", "raw"), [])),
            cls="grid",
        ),
    )
    return ((fh_section),)


def get_project_content(args: Namespace, project: Project) -> dict:
    web_render_methods = []
    for tool, analysis, render_method in iter_report_web_render_methods(args, level="0", required=True):
        web_render_methods.append(("0", tool, analysis, render_method))

    for tool, analysis, render_method in iter_report_web_render_methods(args, level="d", required=False):
        web_render_methods.append(("d", tool, analysis, render_method))

    content = dict()
    for level, tool, analysis, render_method in web_render_methods:
        if scan := Scan.get_most_recent(project, tool, analysis):
            if level_contents := render_method(project=project, scan=scan):
                content[(level, tool, analysis)] = level_contents
    return content


def iter_report_web_render_methods(args: Namespace, level: str, required: bool) -> Iterator:
    for tool_config in args.tools.values():
        for tool, analysis in tool_config.iter_tool_analysis():
            method_name: str = f"{analysis}_{level}"  # e.g. ruff_0, cloc_d or hal_d
            method_module_name: str = f"report.web.{method_name}"
            try:
                method_module: ModuleType = tool_config.import_component(method_module_name)
            except ModuleNotFoundError:
                if required:
                    log.warning(f"Sorry, we couldn't find a {method_module_name=} in ?")
                continue
            try:
                method: Callable = getattr(method_module, method_name)
            except AttributeError:
                log.warning(f"Sorry, have a valid {method_module=} but can't find {method_name=}?")
            yield tool, analysis, method
