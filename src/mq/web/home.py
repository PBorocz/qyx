"""Render the "home"/summary page."""

import logging
from argparse import Namespace
from types import ModuleType
from typing import Callable, Iterator

from fasthtml import common as fh

from mq.constants import ReportLevel
from mq.utils.scoring import get_nested_config
from mq.tools.base import Project, Scan, ToolType
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
        fh.H1("Meta-code Quality - Project Summary"),
        *render_project_selector(request, "/partials/set_project/_main_"),
        fh.Div(id="page-body-content"),
    )


def render_partial_project_summary(request, s_project_id: str):
    """Render the home/summary page."""
    args = request.app.state.args
    if not s_project_id:
        return fh.Section()

    # Find the respective project to display results for
    project = Project.get(Project.id == int(s_project_id))

    # Query all level 0 summaries of raw results *and* derived metrics:
    content = render_all_summary_derived(args, project)

    # Render our grid of results.
    sections = []
    for tool_name in get_nested_config(args.config, "dashboard.tool_order"):
        o_tool = args.tools[tool_name]  # We validated tool-names in setup_configuration!
        for analysis in o_tool.models:
            sections.append(
                fh.Div(
                    fh.Div(fh.Hr(), *content.get((ReportLevel.SUMMARY, o_tool.name, analysis), [])),
                    fh.Div(fh.Hr(), *content.get((ReportLevel.DERIVED, o_tool.name, analysis), [])),
                    cls="grid",
                ),
            )
    return (fh.Section(*sections),)


def render_all_summary_derived(args: Namespace, project: Project) -> dict:
    """Return a dictionary keyed by Level, tool, analysis containing the web render content."""
    web_render_methods = []

    ################################################################################################
    # Lookup "SUMMARY" and "DERIVED" render methods
    ################################################################################################
    for level, required in (
        (ReportLevel.SUMMARY, True),  # All analyses prolly have summary web renderer defined...
        (ReportLevel.DERIVED, False),  # ...but not all them have derived results renderers!
    ):
        for o_tool, analysis, render_method in get_web_render_methods(args, level=level, required=required):
            web_render_methods.append((level, o_tool.name, analysis, render_method))

    ################################################################################################
    # Given the methods, call each renderer and cache contents based on available project & scans.
    ################################################################################################
    content = dict()
    for level, tool_name, analysis, render_method in web_render_methods:
        if scan := Scan.get_most_recent(project, tool_name, analysis):
            if level_contents := render_method(args, project=project, scan=scan):
                content[(level, tool_name, analysis)] = level_contents
    return content


def get_web_render_methods(args: Namespace, level: str, required: bool) -> Iterator:
    for tool_name in get_nested_config(args.config, "dashboard.tool_order"):
        o_tool: ToolType = args.tools[tool_name]
        for analysis in o_tool.models:
            # Lookup the appropriate module that contains the web renderer for tool_module & analysis
            web_method_module: ModuleType = None
            for web_method_module_name in (f"web_{analysis.lower()}", "web"):
                try:
                    web_method_module: ModuleType = o_tool.import_component(web_method_module_name)
                    break
                except ModuleNotFoundError:
                    continue
            if not web_method_module:
                log.warning(
                    f"Sorry, we couldn't find a {web_method_module_name=} in {o_tool.module_name}.web",
                )
                break

            # Using the module, lookup the respective method to render tool_module & analysis
            try:
                method_name: str = f"{analysis.lower()}_{level.value}"  # e.g. ruff_0, cloc_d or hal_d
                method: Callable = getattr(web_method_module, method_name)
            except AttributeError:
                if required:
                    msg = (
                        f"Sorry, we have a valid {web_method_module_name=} "
                        f"{web_method_module=} but can't find {method_name=}?",
                    )
                    log.warning(msg)
                continue

            yield o_tool, analysis, method
