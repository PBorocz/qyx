"""Report data obo running 'fxtd' tool/script."""

from argparse import Namespace
from datetime import datetime

from pygal import DateTimeLine
from pygal.style import Style
from fasthtml import common as fh

from mq.tools.base import Project, Scan

from mq.tools.fxtd.models import query
from mq.web.page import render_page


################################################################################################
# Page layout...
################################################################################################
def render(request, name, config):
    """Do the primary page layout for this tools display page."""
    return render_page(
        request,
        name,
        name.title(),
        *render_project_selector(request),
        # This Div will be updated as the project changes via HTMX!
        fh.Div(id="project-content"),
    )


################################################################################################
# Project Selector
################################################################################################
# FIXME: This is VERY COMMON across all tools, refactor to make it so!
def render_project_selector(request):
    projects = Project.select().order_by(Project.name)
    if not projects:
        return None

    # Convert our project(s) into selector items..
    elif len(projects) > 1:
        fh_select_items = [fh.Option("Project...", value="")]
        for project in projects:
            fh_select_items.append(fh.Option(project.name, value=str(project.id)))

    elif len(projects) == 1:
        project = projects[0]
        fh_select_items = [fh.Option(project.name, value=str(project.id), selected=True)]

    # And return our selector form
    return fh.Form(
        fh.Fieldset(
            fh.Select(
                *fh_select_items,
                name="project",
                aria_label="Select your project...",
                hx_get="/partials/fxtd_set_project",  # HTMX endpoint
                hx_target="#project-content",  # Where to update
                hx_swap="innerHTML",  # How to update
                hx_trigger="load, change",  # Trigger on page load *AND* selection change
            ),
        ),
    )


################################################################################################
# Current Status at 3 Levels
################################################################################################
def render_accordion_levels(request, s_project_id: str = None):
    if not s_project_id:
        return fh.Section()
    args = request.app.state.args
    project = Project.get(Project.id == int(s_project_id))
    scan = Scan.get_most_recent(project, "fxtd", "fxtd")

    return fh.Section(
        fh.H1("Current Status ", fh.Small(f"As Of {scan.as_of_display(full=True)}")),
        fh.Details(fh.Summary("Summary"), name="details", open=True, *render_level_0(args, scan)),
        fh.Details(fh.Summary("By Type"), name="details", *render_level_1(args, scan)),
        fh.Details(fh.Summary("By File"), name="details", *render_level_2(args, scan)),
        cls="bordered",
    )


def render_level_0(args: Namespace, scan: Scan):
    row = query(args, "0", scan=scan)

    t_body = [
        fh.Tr(
            fh.Td("FixMe's & ToDo's Encountered", style="text-align: left"),
            fh.Td(f"{row.count:,d}", style="text-align: right"),
        ),
    ]
    return (
        fh.Table(
            fh.Tbody(*t_body),
            fh.Tfoot(),
            id="fxtd_0",
        ),
        fh.Script("new Tablesort(document.getElementById('fxtd_0'));"),
    )


def render_level_1(args: Namespace, scan: Scan):
    summary = query(args, "0", scan=scan)
    results = query(args, "1", scan=scan)

    t_head = fh.Tr(
        fh.Th("Type", scope="col", style="text-align: left"),
        fh.Th("Count", scope="col", style="text-align: right"),
    )

    t_body = []
    for result in results:
        t_row = fh.Tr(
            fh.Td(result.type, style="text-align: left"),
            fh.Td(f"{result.count:,d}", style="text-align: right"),
        )
        t_body.append(t_row)

    t_total = fh.Tr(
        fh.Td("TOTAL", style="text-align: left"),
        fh.Td(f"{summary.count:,d}", style="text-align: right"),
        fh.Td(""),
    )

    return (
        fh.Table(
            fh.Thead(t_head),
            fh.Tbody(*t_body),
            fh.Tfoot(t_total),
            id="fxtd_1",
        ),
        fh.Script("new Tablesort(document.getElementById('fxtd_1'));"),
    )


def render_level_2(args: Namespace, scan: Scan):
    rows = query(args, "2", scan=scan)

    t_head = fh.Tr(
        fh.Th("Type", scope="col", style="text-align: center"),
        fh.Th("File [line]", scope="col", style="text-align: left"),
        fh.Th("Message", scope="col", style="text-align: left"),
    )

    t_body = []
    for row in rows:
        t_row = fh.Tr(
            fh.Td(row.type, style="text-align: center"),
            fh.Td(f"{row.directory}/{row.filename} [{row.line}]", style="text-align: left"),
            fh.Td(row.message, style="text-align: left"),
        )
        t_body.append(t_row)

    return (
        fh.Table(
            fh.Thead(t_head),
            fh.Tbody(*t_body),
            id="fxtd_2",
        ),
        fh.Script("new Tablesort(document.getElementById('fxtd_2'));"),
    )


################################################################################################
# History
################################################################################################
def render_history_chart(request, s_project_id: str = None):
    # Create Pygal chart
    if not s_project_id:
        return fh.Section()
    project = Project.get(Project.id == int(s_project_id))

    args = request.app.state.args
    args.options.last = 999  # Override to get ALL the data we have!
    timestamps, transposed, rocs = query(args, "history", project=project)

    # FIXME: Make this common across all tools!
    custom_style = Style(
        background="transparent",
        font_family="Inter",
        guide_stroke_color="#cccccc",  # Lighter minor lines
        guide_stroke_dasharray="2,4",  # Different dash for minor
        guide_stroke_width=0.5,  # Thinner minor lines
        major_guide_stroke_color="#333333",  # Darker major lines
        major_guide_stroke_dasharray="6,6",  # Dashed major lines
        major_guide_stroke_width=2,  # Thicker major lines
        transition="400ms ease-in",
    )

    # FIXME: Make a bunch of these COMMON across all tools!
    chart = DateTimeLine(
        y_title="Issues",
        dots_size=1,
        height=500,
        legend_at_bottom=True,
        style=custom_style,
        tooltip_border_radius=10,
        x_label_rotation=45,  # Angle labels to prevent overlap
        x_labels_major_every=2,  # Show every 5th label
        x_value_formatter=lambda dt: dt.strftime("%Y-%m-%d %H:%M"),
    )
    for metric in ("FIXME", "TODO"):
        dt_values = transposed[metric]
        datetime_values = [(datetime.fromisoformat(ts_), count) for ts_, count in dt_values.items()]
        chart.add(metric, datetime_values)

    svg_chart = chart.render()  # Render as SVG and return bytes

    return fh.Section(
        fh.H1("History", style="margin-top: 1rem;"),
        fh.Div(
            fh.NotStr(svg_chart.decode("utf-8")),
            cls="bordered",
        ),
    )
