"""Report data obo running 'radon' tool."""

import logging
from argparse import Namespace

from fasthtml import common as fh

import mq.tools.radon.report_web_renderers as renderers
from mq.tools.base import Project, Scan
from mq.tools.radon.models import RadonHal
from mq.web.page import render_page

log = logging.getLogger("uvicorn")


################################################################################################
# Page layout...
################################################################################################
def render(request, name, config):
    """Do the primary page layout for this tools display page."""
    return render_page(
        request,
        name,
        name.title(),
        *render_selectors(request),
        fh.Div(id="project-content"),  # This Div will be updated as the project changes via HTMX!
    )


################################################################################################
# Selectors
################################################################################################
def render_selectors(request):
    projects = Project.select().order_by(Project.name)
    if not projects:
        return None

    ############################################################################################
    # Convert our project(s) into selector items..
    ############################################################################################
    elif len(projects) > 1:
        fh_select_project = [fh.Option("Project...", value="")]
        for project in projects:
            fh_select_project.append(fh.Option(project.name, value=str(project.id)))

    elif len(projects) == 1:
        project = projects[0]
        fh_select_project = [fh.Option(project.name, value=str(project.id), selected=True)]

    ############################################################################################
    # Convert our project(s) into selector items..
    ############################################################################################
    analyses = (
        ("cc", "Cyclomatic Complexity"),
        ("mi", "Maintainability Index"),
        ("raw", "Raw Metrics"),
        ("hal", "Halstead Complexity Measures"),
    )
    fh_select_analyses = [fh.Option(description, value=value) for value, description in analyses]

    # And return our selector form
    return fh.Form(
        fh.Fieldset(
            fh.Select(
                *fh_select_project,
                name="project",
                aria_label="Select your project...",
                hx_get="/partials/radon_set_project",  # HTMX endpoint
                hx_target="#project-content",  # Where to update
                hx_swap="innerHTML",  # How to update
                hx_trigger="load, change",  # Trigger on page load *AND* selection change
                hx_include="[name='analysis']",  # Include analysis selector value
            ),
            fh.Select(
                *fh_select_analyses,
                name="analysis",
                aria_label="Select your Radon analysis...",
                hx_get="/partials/radon_set_analysis",  # HTMX endpoint
                hx_target="#project-content",  # Where to update
                hx_swap="innerHTML",  # How to update
                hx_trigger="load, change",  # Trigger on page load *AND* selection change
                hx_include="[name='project']",  # Include project selector value
            ),
        ),
    )


################################################################################################
# Current Status at 3 Levels
################################################################################################
def render_accordion_levels(request, s_project_id: str = None, s_analysis: str = None):
    args = request.app.state.args
    project = Project.get(Project.id == int(s_project_id))
    scan = Scan.get_most_recent(project, "radon", s_analysis)
    if not scan:
        log.warning(f"Sorry, no Scan's performed yet for radon:{s_analysis}")
        return fh.Section()

    fh_sections = [
        fh.H1("Current Status ", fh.Small(f"As Of {scan.as_of_display(collapse_today=True)}")),
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
            return renderers.cc_0(args, scan)
        case "hal":
            return renderers.hal_0(args, scan)
        case "mi":
            return renderers.mi_0(args, scan)
        case "raw":
            return renderers.raw_0(args, scan)
        case _:
            return fh.Section()


def render_level_1(args: Namespace, scan: Scan):
    match scan.analysis.lower():
        case "cc":
            return renderers.cc_1(args, scan)
        case "hal":
            return renderers.hal_1(args, scan)
        case "mi":
            return renderers.mi_1(args, scan)
        case "raw":
            return renderers.raw_1(args, scan)
        case _:
            return fh.Section()


def render_level_2(args: Namespace, scan: Scan):
    match scan.analysis.lower():
        case "cc":
            return renderers.cc_2(args, scan)
        case "hal":
            return renderers.hal_2(args, scan)
        case "mi":
            return renderers.mi_2(args, scan)
        case "raw":
            return renderers.raw_2(args, scan)
        case _:
            return fh.Section()


def render_level_3(args: Namespace, scan: Scan):
    match scan.analysis.lower():
        case "cc":
            return renderers.cc_3(args, scan)
        case "hal":
            return renderers.hal_3(args, scan)
        case _:
            return fh.Section()


################################################################################################
# History
################################################################################################
def render_history_chart(request, s_project_id: str = None, s_analysis: str = None):
    args = request.app.state.args
    project = Project.get(Project.id == int(s_project_id))

    match s_analysis.lower():
        case "cc":
            single = True
            chart = renderers.cc_h(args, project)
        case "hal":
            single = False
            charts = renderers.hal_h(args, project)
        case "mi":
            single = True
            chart = renderers.mi_h(args, project)
        case "raw":
            single = True
            chart = renderers.raw_h(args, project)
        case _:
            raise RuntimeError(f"Sorry, unrecognised {s_analysis=}")

    if single:
        return fh.Section(
            fh.H1("History", style="margin-top: 1rem;"),
            fh.Div(
                fh.NotStr(chart.render().decode("utf-8")),
                cls="bordered",
            ),
        )

    # Halstead gets special treatment due to the number of metrics available:
    fh_sections = [
        fh.H1("History...", style="margin-top: 1rem;"),
        fh.Form(
            fh.Fieldset(
                fh.Select(
                    *[fh.Option(t_attr[0].split("(")[0], value=t_attr[1]) for t_attr in RadonHal.attrs()],
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
                fh.NotStr(chart.render().decode("utf-8")),
                id=f"metric-{metric}",
                style=f"display: {'block' if metric == 'bugs' else 'none'};",
            ),
        )
    return fh.Section(*fh_sections)
