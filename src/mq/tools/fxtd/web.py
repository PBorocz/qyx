"""Report data obo running 'fxtd' tool/script."""

from argparse import Namespace
from datetime import datetime

from fasthtml import common as fh
from pygal import DateTimeLine
from pygal.style import Style

from mq.tools.base import Project, Scan
from mq.tools.fxtd.models import query
from mq.web import DEFAULT_CHART_STYLE, render_project_selector
from mq.web.page import render_page


################################################################################################
# Page layout...
################################################################################################
def render(request, name, config):
    """Do the primary page layout for this tools display page."""
    return render_page(
        request,
        name.title(),
        name,
        *render_project_selector(request, "/partials/set_project/fxtd"),
        fh.Div(id="page-body-content"),
    )


################################################################################################
def render_content(args: Namespace, request, s_project_id: str = None, analysis: str = None):
    """Render the content portion (ie. body) of the page."""
    return (
        *_render_current(args, request, s_project_id, analysis),
        *_render_history(args, request, s_project_id, analysis),
    )


def _render_current(args: Namespace, request, s_project_id: str = None, analysis: str = None):
    """Render the current status portion of the page."""
    if not s_project_id:
        return fh.Section()
    project = Project.get(Project.id == int(s_project_id))
    scan = Scan.get_most_recent(project, "fxtd", "fxtd")

    return fh.Section(
        fh.H1("Current Status ", fh.Small(f"As Of {scan.as_of_display(collapse_today=True)}")),
        fh.Details(fh.Summary("Summary"), name="details", open=True, *fxtd_0(args, scan)),
        fh.Details(fh.Summary("By Directory"), name="details", *fxtd_1(args, scan)),
        fh.Details(fh.Summary("By File"), name="details", *fxtd_2(args, scan)),
        cls="bordered",
    )


def _render_history(args: Namespace, request, s_project_id: str = None, analysis: str = None):
    """Render the history portion of the page."""
    # Create Pygal chart
    if not s_project_id:
        return fh.Section()
    project = Project.get(Project.id == int(s_project_id))
    chart = fxtd_h(args, project)
    return fh.Section(
        fh.H1("History", style="margin-top: 1rem;"),
        fh.Div(fh.NotStr(chart.decode("utf-8")), cls="bordered"),
    )


def fxtd_0(args: Namespace, scan: Scan, project: Project = None):
    results = query(args, "0", scan=scan)
    if not results:
        return None

    grand_total = sum([result.count for result in results])

    t_head = fh.Tr(
        fh.Th("Type", scope="col", style="text-align: left"),
        fh.Th("Count", scope="col", style="text-align: right"),
    )

    t_body = []
    for result in results:
        t_row = fh.Tr(
            fh.Th(result.type, style="text-align: left"),
            fh.Th(f"{result.count:,d}", style="text-align: right"),
        )
        t_body.append(t_row)

    t_total = fh.Tr(
        fh.Th("TOTAL", style="text-align: left"),
        fh.Th(f"{grand_total:,d}", style="text-align: right"),
        fh.Td(""),
    )

    return (
        fh.Table(
            fh.Thead(t_head),
            fh.Tbody(*t_body),
            fh.Tfoot(t_total),
            id="fxtd_0",
        ),
    )


def fxtd_1(args: Namespace, scan: Scan, project: Project = None):
    results = query(args, "1", scan=scan)
    grand_total = sum([result.count for result in results])

    t_head = fh.Tr(
        fh.Th("Type", scope="col", style="text-align: left"),
        fh.Th("Directory", scope="col", style="text-align: left"),
        fh.Th("Count", scope="col", style="text-align: right"),
    )

    t_body = []
    for result in results:
        t_row = fh.Tr(
            fh.Td(result.type, style="text-align: left"),
            fh.Td(result.directory, style="text-align: right"),
            fh.Td(f"{result.count:,d}", style="text-align: right"),
        )
        t_body.append(t_row)

    t_total = fh.Tr(
        fh.Td("TOTAL", style="text-align: left"),
        fh.Td(""),
        fh.Td(f"{grand_total:,d}", style="text-align: right"),
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


def fxtd_2(args: Namespace, scan: Scan, project: Project = None):
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


def fxtd_d(args: Namespace, project: Project, scan: Scan):
    rows, composite = query(args, "d", project=project, scan=scan)
    if not rows or not composite:
        return None
    t_head = fh.Tr(
        fh.Th("Metric", scope="col", style="text-align: left"),
        fh.Th("Value", scope="col", style="text-align: right"),
        fh.Th("Grade", scope="col", style="text-align: center"),
    )

    t_body = []
    for row in rows:
        t_row = fh.Tr(
            fh.Td(f"{row.type}'s per kLOC", style="text-align: left"),
            fh.Td(f"{row.fxtd_d.score:.2f}", style="text-align: right"),
            fh.Td(
                f"{row.fxtd_d.grade}",
                style=f"text-align: center; color: var(--pico-muted-color); background-color: {row.fxtd_d.color}",
            ),
        )
        t_body.append(t_row)

    t_foot = fh.Tr(
        fh.Th("Composite (weighted)", scope="col", style="text-align: left"),
        fh.Td(f"{composite.score:.2f}", style="text-align: right"),
        fh.Td(
            f"{composite.grade}",
            style=f"text-align: center; color: var(--pico-muted-color); background-color: {composite.color}",
        ),
    )

    return (
        fh.Table(
            fh.Thead(t_head),
            fh.Tbody(*t_body),
            fh.Tfoot(*t_foot),
        ),
    )


def fxtd_h(args: Namespace, project: Project, scan: Scan = None):
    # Create Pygal chart
    timestamps, transposed, rocs = query(args, "h", project=project)

    style = Style(**DEFAULT_CHART_STYLE)

    chart = DateTimeLine(
        y_title="Instances",
        dots_size=1,
        height=500,
        legend_at_bottom=True,
        style=style,
        tooltip_border_radius=10,
        x_label_rotation=45,  # Angle labels to prevent overlap
        x_labels_major_every=2,  # Show every 5th label
        x_value_formatter=lambda dt: dt.strftime("%Y-%m-%d %H:%M"),
    )
    for metric in ("FIXME", "TODO"):
        dt_values = transposed[metric]
        datetime_values = [(datetime.fromisoformat(ts_), count) for ts_, count in dt_values.items()]
        chart.add(metric, datetime_values)

    return chart.render()  # Render as SVG and return bytes
