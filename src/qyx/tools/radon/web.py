"""Report data obo running 'radon' tool."""

import logging
from argparse import Namespace

from bottle import request

from qyx.tools.base import Project, Scan, State
from qyx.tools.radon.web_cc import cc_0, cc_1, cc_2, cc_3, cc_d, cc_h
from qyx.tools.radon.web_hal import hal_0, hal_1, hal_2, hal_3, hal_d, hal_h
from qyx.tools.radon.web_mi import mi_0, mi_1, mi_2, mi_d, mi_h
from qyx.tools.radon.web_raw import raw_0, raw_1, raw_2, raw_h
from qyx.web import get_analysis_selector, get_project_selector
from qyx.web.page import render_page, render_partial

log = logging.getLogger(__name__)


################################################################################################
# Page layout...
################################################################################################
def render(template: str = "radon::pages/main.html") -> str:
    """Render the tool's primary page."""
    return render_page(
        "QYX-RADON",
        template,
        project_options=get_project_selector(),
        analysis_options=get_analysis_selector(),
        set_project="/partials/set_project/radon",
        set_analysis="/partials/set_project/radon",
    )


def render_content() -> str:
    """Render the content portion (ie. body) of the page."""
    args = request.app.args

    # Get the arguments passed from the HTMX get context:
    s_project_id = request.query.project
    analysis = request.query.analysis.lower()

    # Find the project...
    project = Project.get(Project.id == int(s_project_id))
    if not s_project_id or not project:
        return render_partial("base::fragments/_no_project_yet.html")

    # Find the most recent scan on behalf of this project...
    scan = Scan.get_most_recent(project, "radon", analysis)
    if not scan:
        return render_partial("base::fragments/_no_scans_yet.html")

    # Populate the return context with all the data and charts
    # necessary to render the page's body:
    context = Namespace()
    context.level_0 = _query_level(args, "0", project, scan, analysis)  # NOTE: Some of these might return None
    context.level_1 = _query_level(args, "1", project, scan, analysis)  # if the level is not applicable or
    context.level_2 = _query_level(args, "2", project, scan, analysis)  # defined for the respective analysis,
    context.level_3 = _query_level(args, "3", project, scan, analysis)  # and that's OK!
    context.level_d = _query_level(args, "d", project, scan, analysis)
    context.chart_h = _query_level(args, "h", project, scan, analysis)
    context.as_of = scan.as_of_display(collapse_today=True)

    # Remember what we just processed for next time through (used by
    # the get_project/analysis_selector's above)
    State.update(args, project=project.name, analysis=analysis)

    # Template to return is based on the particular analysis requested:
    template: str = f"radon::{analysis}/fragments/body.html"

    return render_partial(template, **context.__dict__)


def _query_level(args: Namespace, level: str, project: Project, scan: Scan, analysis: str) -> dict | None:
    """Get data associated with the specified level for the given project and scan's analysis type."""
    # FIXME: Using the level as an int IS A BIT OF A SHORTCUT! Revisit when we move level enum to non ints.
    # Mapping between analysis & reporting level to data query method
    query_methods_by_analysis = {
        "cc": {
            "0": cc_0,
            "1": cc_1,
            "2": cc_2,
            "3": cc_3,
            "d": cc_d,
            "h": cc_h,
        },
        "hal": {
            "0": hal_0,
            "1": hal_1,
            "2": hal_2,
            "3": hal_3,
            "d": hal_d,
            "h": hal_h,
        },
        "mi": {
            "0": mi_0,
            "1": mi_1,
            "2": mi_2,
            "d": mi_d,
            "h": mi_h,
        },
        "raw": {
            "0": raw_0,
            "1": raw_1,
            "2": raw_2,
            "h": raw_h,
        },
    }
    if analysis not in query_methods_by_analysis:  # LBYL
        return None
    analysis_methods = query_methods_by_analysis[analysis]

    if level not in analysis_methods:
        return None
    analysis_method = analysis_methods[level]

    return analysis_method(args, project, scan)
