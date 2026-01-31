"""Report data obo running 'radon' tool."""

import logging
from argparse import Namespace

from fasthtml import common as fh

from mq.tools.base import Project, Scan
from mq.tools.radon.models import RadonHal
from mq.tools.radon.web_cc import cc_0, cc_1, cc_2, cc_3, cc_h
from mq.tools.radon.web_hal import hal_0, hal_1, hal_2, hal_3, hal_h
from mq.tools.radon.web_mi import mi_0, mi_1, mi_2, mi_h
from mq.tools.radon.web_raw import raw_0, raw_1, raw_2, raw_h
from mq.web import get_project_select
from mq.web.page import render_page

log = logging.getLogger("uvicorn")


################################################################################################
# Page layout...
################################################################################################
def render(request, name, config):
    """Do the primary page layout for this tools display page."""
    return render_page(
        request,
        name.title(),
        name,
        *render_selectors(request, "/partials/set_project/radon"),
        fh.Div(id="page-body-content"),  # This Div will be updated as the project changes via HTMX!
    )


################################################################################################
def render_content(args: Namespace, request, s_project_id: str = None, analysis: str = None):
    """Render the content portion (ie. body) of the page."""
    return (
        *_render_current(args, request, s_project_id, analysis),
        *_render_history(args, request, s_project_id, analysis),
    )


def _render_current(args: Namespace, request, s_project_id: str = None, analysis: str = None):
    """Render current status at 3 Levels."""
    if not s_project_id:
        return fh.Section()

    project = Project.get(Project.id == int(s_project_id))
    scan = Scan.get_most_recent(project, "radon", analysis)
    if not scan:
        log.warning(f"Sorry, no Scan's performed yet for radon:{analysis}")
        return fh.Section()

    fh_sections = [
        fh.H1("Current Status ", fh.Small(f"As Of {scan.as_of_display()}")),
        fh.Details(fh.Summary("Summary"), name="details", open=True, *render_level_0(args, scan)),
        fh.Details(fh.Summary("By Directory"), name="details", *render_level_1(args, scan)),
        fh.Details(fh.Summary("By File"), name="details", *render_level_2(args, scan)),
    ]
    if scan.analysis.lower() in ("cc", "hal"):
        fh_sections.append(
            fh.Details(fh.Summary("By Item"), name="details", *render_level_3(args, scan)),
        )
    return fh.Section(*fh_sections, cls="bordered")


# FIXME: Can we make these more dynamic?
def render_level_0(args: Namespace, scan: Scan):
    match scan.analysis.lower():
        case "cc":
            return cc_0(args, scan)
        case "hal":
            return hal_0(args, scan)
        case "mi":
            return mi_0(args, scan)
        case "raw":
            return raw_0(args, scan)
        case _:
            return fh.Section()


def render_level_1(args: Namespace, scan: Scan):
    match scan.analysis.lower():
        case "cc":
            return cc_1(args, scan)
        case "hal":
            return hal_1(args, scan)
        case "mi":
            return mi_1(args, scan)
        case "raw":
            return raw_1(args, scan)
        case _:
            return fh.Section()


def render_level_2(args: Namespace, scan: Scan):
    match scan.analysis.lower():
        case "cc":
            return cc_2(args, scan)
        case "hal":
            return hal_2(args, scan)
        case "mi":
            return mi_2(args, scan)
        case "raw":
            return raw_2(args, scan)
        case _:
            return fh.Section()


def render_level_3(args: Namespace, scan: Scan):
    match scan.analysis.lower():
        case "cc":
            return cc_3(args, scan)
        case "hal":
            return hal_3(args, scan)
        case _:
            return fh.Section()


################################################################################################
def _render_history(args: Namespace, request, s_project_id: str = None, analysis: str = None):
    """Render History portion of the page."""
    if not s_project_id:
        return fh.Section()
    if not analysis:
        return fh.Section(fh.P("Sorry, no analysis selected yet"))

    project = Project.get(Project.id == int(s_project_id))

    match analysis.lower():
        case "cc":
            single = True
            chart = cc_h(args, project)
        case "hal":
            single = False
            charts = hal_h(args, project)
        case "mi":
            single = True
            chart = mi_h(args, project)
        case "raw":
            single = True
            chart = raw_h(args, project)
        case _:
            raise RuntimeError(f"Sorry, unrecognised {analysis=}")

    if single:
        return fh.Section(
            fh.H1("History", style="margin-top: 1rem;"),
            fh.Div(
                fh.NotStr(chart.decode("utf-8")),
                cls="bordered",
            ),
        )

    # Halstead gets special treatment due to the number of metrics available:
    fh_sections = [
        fh.H1("History...", style="margin-top: 1rem;"),
        fh.Form(
            fh.Fieldset(
                fh.Select(
                    *[fh.Option(attr.display, value=attr.name) for attr in RadonHal.attrs()],
                    onchange="showChart(this.value)",  # this.value/value "h1", "N1", "bugs", etc.
                    style="max-width: 300px; margin-bottom: 2rem;",
                ),
            ),
        ),
        fh.Script("""
            function showChart(metric) {
                // Hide all charts
                document.querySelectorAll('[id^="metric-"]').forEach(chart => {
                    // console.log('Hiding:', chart.id);
                    chart.style.display = 'none';
                });

                // Show selected chart
                const chartId = 'metric-' + metric;
                // console.log('Looking for:', chartId);

                const selectedChart = document.getElementById(chartId);
                // console.log('Found chart:', selectedChart);

                if (selectedChart) {
                    selectedChart.style.display = 'block';
                }
            }
        """),
    ]
    for metric, chart in charts.items():
        fh_sections.append(
            fh.Div(
                fh.NotStr(chart.decode("utf-8")),
                id=f"metric-{metric}",
                style=f"display: {'block' if metric == 'bugs' else 'none'};",
            ),
        )
    return fh.Section(*fh_sections)


################################################################################################
# Selectors
################################################################################################
def render_selectors(request, hx_get: str):
    ############################################################################################
    # Get our (generic) project selector widget
    ############################################################################################
    fh_select_project = get_project_select(request, hx_get)

    ############################################################################################
    # Get radon-specific analysis selector
    ############################################################################################
    analyses = (
        ("cc", "Cyclomatic Complexity"),
        ("mi", "Maintainability Index"),
        ("raw", "Raw Metrics"),
        ("hal", "Halstead Complexity Measures"),
    )
    fh_select_analyses = [fh.Option(description, value=value) for value, description in analyses]

    # And return our COMBINED selector form (ie. across both projects and analyses)
    return fh.Form(
        fh.Fieldset(
            fh_select_project,
            fh.Select(
                *fh_select_analyses,
                name="analysis",
                aria_label="Select your Radon analysis...",
                hx_get="/partials/set_project/radon",  # HTMX endpoint
                hx_target="#page-body-content",  # Where to update
                hx_swap="innerHTML",  # How to update
                hx_trigger="load, change",  # Trigger on page load *AND* selection change
                hx_include="[name='project']",  # Include project selector value
            ),
        ),
    )
