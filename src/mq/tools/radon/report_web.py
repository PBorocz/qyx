"""Report data obo running 'radon' tool."""

import logging
from argparse import Namespace
from datetime import datetime

from pygal import DateTimeLine
from pygal.style import Style
from fasthtml import common as fh

from mq.tools.base import Project, Scan

import mq.tools.radon.report_web_renderers as renderers
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
        ("raw", "Code Counts"),
        ("hal", "Halstead"),
        ("mi", "Maintainability"),
        ("cc", "Cyclomatic Complexity"),
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
        fh.H1("Current Status ", fh.Small(f"As Of {scan.as_of_display(full=True)}")),
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
def render_history_chart(request, s_project_id: str = None): ...


# def render_history_chart(request, s_project_id: str = None):
#     # Create Pygal chart
#     if not s_project_id:
#         return fh.Section()
#     project = Project.get(Project.id == int(s_project_id))
#     args = request.app.state.args
#     args.options.last = 999  # Override to get ALL the data we have!
#     _, rows, _ = query(args, "history", project=project)

#     # FIXME: Make this common across all tools!
#     custom_style = Style(
#         background="transparent",
#         font_family="Inter",
#         guide_stroke_color="#cccccc",  # Lighter minor lines
#         guide_stroke_dasharray="2,4",  # Different dash for minor
#         guide_stroke_width=0.5,  # Thinner minor lines
#         major_guide_stroke_color="#333333",  # Darker major lines
#         major_guide_stroke_dasharray="6,6",  # Dashed major lines
#         major_guide_stroke_width=2,  # Thicker major lines
#         transition="400ms ease-in",
#     )

#     # FIXME: Make a bunch of these COMMON across all tools!
#     chart = DateTimeLine(
#         y_title="Radon ...",
#         dots_size=1,
#         height=500,
#         show_legend=False,
#         style=custom_style,
#         tooltip_border_radius=10,
#         x_label_rotation=45,  # Angle labels to prevent overlap
#         x_labels_major_every=2,  # Show every 5th label
#         x_value_formatter=lambda dt: dt.strftime("%Y-%m-%d %H:%M"),
#     )
#     datetime_values = [(datetime.fromisoformat(ts_), count) for ts_, count in rows.items()]

#     chart.add("-count-", datetime_values)

#     svg_chart = chart.render()  # Render as SVG and return bytes

#     return fh.Section(
#         fh.H1("History", style="margin-top: 1rem;"),
#         fh.Div(
#             fh.NotStr(svg_chart.decode("utf-8")),
#             cls="bordered",
#         ),
#     )
