"""Render the "home"/summary page."""

import logging
from argparse import Namespace
from types import ModuleType
from typing import Callable, Iterator

from fasthtml import common as fh

from mq.constants import ReportLevel
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

    # Query all level 0 summaries of raw results *and* derived metrics:
    content = get_project_content(request.app.state.args, project)

    # Render our grid of results.
    # TODO: Ultimately would be great to have this dynamically created!
    fh_section = fh.Section(
        fh.Div(
            fh.Div(fh.H3("Raw Metrics")),
            fh.Div(fh.H3("Derived Metrics")),
            cls="grid",
        ),
        fh.Div(
            fh.Div(*content.get((ReportLevel.SUMMARY, "cloc", "cloc"), [])),
            fh.Div(*content.get((ReportLevel.DERIVED, "cloc", "cloc"), [])),
            cls="grid",
        ),
        fh.Div(
            fh.Div(*content.get((ReportLevel.SUMMARY, "ruff", "ruff"), [])),
            fh.Div(*content.get((ReportLevel.DERIVED, "ruff", "ruff"), [])),
            cls="grid",
        ),
        fh.Div(
            fh.Div(*content.get((ReportLevel.SUMMARY, "fxtd", "fxtd"), [])),
            fh.Div(*content.get((ReportLevel.DERIVED, "fxtd", "fxtd"), [])),
            cls="grid",
        ),
        fh.Div(
            fh.Div(*content.get((ReportLevel.SUMMARY, "radon", "mi"), [])),
            fh.Div(*content.get((ReportLevel.DERIVED, "radon", "mi"), [])),
            cls="grid",
        ),
        fh.Div(
            fh.Div(*content.get((ReportLevel.SUMMARY, "radon", "cc"), [])),
            fh.Div(*content.get((ReportLevel.DERIVED, "radon", "cc"), [])),
            cls="grid",
        ),
        fh.Div(
            fh.Div(*content.get((ReportLevel.SUMMARY, "radon", "hal"), [])),
            fh.Div(*content.get((ReportLevel.DERIVED, "radon", "hal"), [])),
            cls="grid",
        ),
        fh.Div(
            fh.Div(*content.get((ReportLevel.SUMMARY, "radon", "raw"), [])),
            fh.Div(*content.get((ReportLevel.DERIVED, "radon", "raw"), [])),
            cls="grid",
        ),
    )
    return ((fh_section),)


def get_project_content(args: Namespace, project: Project) -> dict:
    web_render_methods = []

    # "SUMMARY level results...
    for tool, analysis, render_method in iter_report_web_render_methods(
        args,
        level=ReportLevel.SUMMARY,
        required=True,
    ):
        web_render_methods.append((ReportLevel.SUMMARY, tool, analysis, render_method))

    # "Derived" results...
    for tool, analysis, render_method in iter_report_web_render_methods(
        args,
        level=ReportLevel.DERIVED,
        required=False,
    ):
        web_render_methods.append((ReportLevel.DERIVED, tool, analysis, render_method))

    content = dict()
    for level, tool, analysis, render_method in web_render_methods:
        # log.info(f"Considering: {project.id=} {level=} {tool=} {analysis=} {render_method=}")
        if scan := Scan.get_most_recent(project, tool, analysis):
            # log.info(f"Matching scan: {scan.id=}")
            if level_contents := render_method(args, project=project, scan=scan):
                content[(level, tool, analysis)] = level_contents
    return content


def iter_report_web_render_methods(args: Namespace, level: str, required: bool) -> Iterator:
    for tool_config in args.tools.values():
        for tool, analysis in tool_config.iter_tool_analysis():
            # log.info(f"{tool=} {analysis=}")
            method_module = None
            for method_module_name in (f"web_{analysis.lower()}", "web"):
                try:
                    method_module: ModuleType = tool_config.import_component(method_module_name)
                    # log.info(f"Found! {method_module=}")
                    break
                except ModuleNotFoundError:
                    continue
            if not method_module:
                log.warning(
                    f"Sorry, We couldn't find a {method_module_name=} in {tool_config.module_name}.web",
                )
                break

            try:
                method_name: str = f"{analysis}_{level.value}"  # e.g. ruff_0, cloc_d or hal_d
                method: Callable = getattr(method_module, method_name)
                # log.info(f"Found! {method_name=} {method=}")
            except AttributeError:
                if required:
                    log.warning(
                        f"Sorry, have a valid {method_module_name=} {method_module=} but can't find {method_name=}?"
                    )
                continue

            yield tool, analysis, method
