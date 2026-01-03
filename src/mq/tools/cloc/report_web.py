"""Report data obo running 'cloc' tool."""

from argparse import Namespace
from datetime import datetime

from pygal import DateTimeLine
from pygal.style import Style
from fasthtml import common as fh

from mq.tools.base import Project, Scan

from mq.tools.cloc.models import query
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
                hx_get="/partials/cloc_set_project",  # HTMX endpoint
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
    scan = Scan.get_most_recent(project, "cloc", "cloc")

    return fh.Section(
        fh.H1("Current Status"),
        fh.H4(f"As Of {scan.as_of_display(full=False)}"),
        fh.Details(fh.Summary("Summary"), name="details", open=True, *render_level_0(args, scan)),
        fh.Details(fh.Summary("By Directory"), name="details", *render_level_1(args, scan)),
        fh.Details(fh.Summary("By File"), name="details", *render_level_2(args, scan)),
        cls="bordered",
    )


def render_level_0(args: Namespace, scan: Scan):
    results = query(args, "0", scan=scan)
    return (
        fh.Table(
            fh.Thead(
                fh.Tr(
                    fh.Th("Lines of Code", scope="col", style="text-align: right"),
                    fh.Th("Comment Lines", scope="col", style="text-align: right"),
                    fh.Th("Blank Lines", scope="col", style="text-align: right"),
                    fh.Th("TOTAL", scope="col", style="text-align: right"),
                ),
            ),
            fh.Tbody(
                fh.Tr(
                    fh.Td(f"{results.lines_code:,d}", style="text-align: right"),
                    fh.Td(f"{results.lines_comment:,d}", style="text-align: right"),
                    fh.Td(f"{results.lines_blank:,d}", style="text-align: right"),
                    fh.Td(f"{results.lines_total:,d}", style="text-align: right"),
                ),
            ),
        ),
    )


def render_level_1(args: Namespace, scan: Scan):
    grand_total = query(args, "0", scan=scan)
    detail_rows = query(args, "1", scan=scan)

    t_head = fh.Tr(
        fh.Th("Directory", scope="col", style="text-align: left"),
        fh.Th("Lines of Code", scope="col", style="text-align: right"),
        fh.Th("Comment Lines", scope="col", style="text-align: right"),
        fh.Th("Blank Lines", scope="col", style="text-align: right"),
        fh.Th("TOTAL", scope="col", style="text-align: right"),
    )

    t_body = []
    for result in detail_rows:
        t_row = fh.Tr(
            fh.Td(result.directory, style="text-align: left"),
            fh.Td(f"{result.lines_code:,d}", style="text-align: right"),
            fh.Td(f"{result.lines_comment:,d}", style="text-align: right"),
            fh.Td(f"{result.lines_blank:,d}", style="text-align: right"),
            fh.Td(f"{result.lines_total:,d}", style="text-align: right"),
        )
        t_body.append(t_row)

    t_total = fh.Tr(
        fh.Td("TOTAL", style="text-align: left"),
        fh.Td(f"{grand_total.lines_code:,d}", style="text-align: right"),
        fh.Td(f"{grand_total.lines_comment:,d}", style="text-align: right"),
        fh.Td(f"{grand_total.lines_blank:,d}", style="text-align: right"),
        fh.Td(f"{grand_total.lines_total:,d}", style="text-align: right"),
    )

    return (
        fh.Table(
            fh.Thead(t_head),
            fh.Tbody(*t_body),
            fh.Tfoot(t_total),
            id="level_1",
        ),
        fh.Script("new Tablesort(document.getElementById('level_1'));"),
    )


def render_level_2(args: Namespace, scan: Scan):
    results, column_totals, grand_total = query(args, "2", scan=scan)

    t_head = fh.Tr(
        fh.Th("File", scope="col", style="text-align: left"),
        fh.Th("Lines of Code", scope="col", style="text-align: right"),
        fh.Th("Comment Lines", scope="col", style="text-align: right"),
        fh.Th("Blank Lines", scope="col", style="text-align: right"),
        fh.Th("TOTAL", scope="col", style="text-align: right"),
    )

    t_body = []
    for result in results:
        t_row = fh.Tr(
            fh.Td(f"{result.directory}/{result.filename}", style="text-align: left"),
            fh.Td(f"{result.lines_code:,d}", style="text-align: right"),
            fh.Td(f"{result.lines_comment:,d}", style="text-align: right"),
            fh.Td(f"{result.lines_blank:,d}", style="text-align: right"),
            fh.Td(f"{result.lines_total:,d}", style="text-align: right"),
        )
        t_body.append(t_row)

    t_total = fh.Tr(
        fh.Td("TOTAL", style="text-align: left"),
        fh.Td(f"{column_totals['lines_code']:,d}", style="text-align: right"),
        fh.Td(f"{column_totals['lines_comment']:,d}", style="text-align: right"),
        fh.Td(f"{column_totals['lines_blank']:,d}", style="text-align: right"),
        fh.Td(f"{grand_total:,d}", style="text-align: right"),
    )

    return (
        fh.Table(
            fh.Thead(t_head),
            fh.Tbody(*t_body),
            fh.Tfoot(t_total),
            id="level_2",
        ),
        fh.Script("new Tablesort(document.getElementById('level_2'));"),
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
    _, rows, _, _, _, _ = query(args, "history", project=project)

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

    chart = DateTimeLine(
        y_title="Lines",
        dots_size=1,
        height=500,
        legend_at_bottom=True,
        legend_at_bottom_columns=3,
        style=custom_style,
        tooltip_border_radius=10,
        x_label_rotation=45,  # Angle labels to prevent overlap
        x_labels_major_every=2,  # Show every 5th label
        x_value_formatter=lambda dt: dt.strftime("%Y-%m-%d %H:%M"),
    )
    datetime_values_cd = [(datetime.fromisoformat(row.timestamp), row.total_code) for row in rows]
    datetime_values_cm = [(datetime.fromisoformat(row.timestamp), row.total_comment) for row in rows]
    datetime_values_bl = [(datetime.fromisoformat(row.timestamp), row.total_blank) for row in rows]

    chart.add("Code", datetime_values_cd)
    chart.add("Comments", datetime_values_cm)
    chart.add("Blanks", datetime_values_bl)

    svg_chart = chart.render()  # Render as SVG and return bytes

    return fh.Section(
        fh.H1("History", style="margin-top: 1rem;"),
        fh.Div(
            fh.NotStr(svg_chart.decode("utf-8")),
            cls="bordered",
        ),
    )
