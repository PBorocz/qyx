"""Render web data obo running 'ruff' tool."""

from argparse import Namespace
from datetime import datetime

from fasthtml import common as fh
from pygal import DateTimeLine
from pygal.style import Style

from mq.constants import ReportLevel
from mq.tools.base import Project, Scan
from mq.tools.ruff import get_ruff_rule_name
from mq.tools.ruff.models import query
from mq.web import DEFAULT_CHART_STYLE, render_project_selector
from mq.web.page import render_page


################################################################################################
# Page layout...
################################################################################################
def render(request, name, config):
    """Render the primary page layout for this tools display page."""
    return render_page(
        request,
        name.title(),
        name,
        *render_project_selector(request, "/partials/set_project/ruff"),
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
    scan = Scan.get_most_recent(project, "ruff", "ruff")

    return fh.Section(
        fh.H1("Current Status ", fh.Small(f"As Of {scan.as_of_display(collapse_today=True)}")),
        fh.Details(fh.Summary("Summary"), name="details", open=True, *ruff_0(args, scan)),
        fh.Details(fh.Summary("By Rule"), name="details", open=False, *ruff_1(args, scan)),
        fh.Details(fh.Summary("By File"), name="details", open=False, *ruff_2(args, scan)),
        cls="bordered",
    )


def _render_history(args: Namespace, request, s_project_id: str = None, analysis: str = None):
    """Render the history portion of the page."""
    # Create Pygal chart
    if not s_project_id:
        return fh.Section()
    project = Project.get(Project.id == int(s_project_id))
    chart = ruff_h(args, project)
    return fh.Section(
        fh.H1("History", style="margin-top: 1rem;"),
        fh.Div(fh.NotStr(chart.decode("utf-8")), cls="bordered"),
    )


def ruff_0(args: Namespace, scan: Scan, **kwargs):
    row = query(args, ReportLevel.SUMMARY, scan=scan)
    return (
        fh.Table(
            fh.Thead(
                fh.Tr(
                    fh.Th("Ruff", style="text-align: left", colspan=ReportLevel.FILE),
                ),
            ),
            fh.Tbody(
                fh.Tr(
                    fh.Th("Issues", style="text-align: left"),
                    fh.Td(f"{int(row.count):,d}", style="text-align: right"),
                ),
            ),
        ),
    )


def ruff_1(args: Namespace, scan: Scan, project: Project = None):
    summary = query(args, ReportLevel.SUMMARY, scan=scan)
    results = query(args, ReportLevel.DIRECTORY, scan=scan)

    t_head = fh.Tr(
        fh.Th("Rule", scope="col", style="text-align: left"),
        fh.Th("Count", scope="col", style="text-align: right"),
        fh.Th("Message", scope="col", style="text-align: left"),
    )

    t_body = []
    for result in results:
        rule_name = get_ruff_rule_name(result.rule_code)
        t_row = fh.Tr(
            fh.Td(result.rule_code, style="text-align: left"),
            fh.Td(f"{result.count:,d}", style="text-align: right"),
            fh.Td(rule_name.title(), style="text-align: left"),
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
            id="level_1",
        ),
        fh.Script("new Tablesort(document.getElementById('level_1'));"),
    )


def ruff_2(args: Namespace, scan: Scan, project: Project = None):
    rows = query(args, ReportLevel.FILE, scan=scan)

    t_head = fh.Tr(
        fh.Th("Rule", scope="col", style="text-align: left"),
        fh.Th("File [line]", scope="col", style="text-align: left"),
        fh.Th("Message", scope="col", style="text-align: left"),
    )

    t_body = []
    for row in rows:
        t_row = fh.Tr(
            fh.Td(row.rule_code, style="text-align: left"),
            fh.Td(f"{row.directory}/{row.filename} [{row.line}]", style="text-align: left"),
            fh.Td(row.message, style="text-align: left"),
        )
        t_body.append(t_row)

    return (
        fh.Table(
            fh.Thead(t_head),
            fh.Tbody(*t_body),
            id="level_2",
        ),
        fh.Script("new Tablesort(document.getElementById('level_2'));"),
    )


def ruff_d(args: Namespace, project: Project, scan: Scan):
    """Report on derived ruff metrics."""
    row = query(args, ReportLevel.DERIVED, project=project, scan=scan)
    if not row.violations_per_kloc:
        return ()
    return (
        fh.Table(
            fh.Thead(
                fh.Tr(
                    fh.Th("Metric", scope="col", style="text-align: left"),
                    fh.Th("Value", scope="col", style="text-align: center"),
                    fh.Th("Grade", scope="col", style="text-align: center"),
                ),
            ),
            fh.Tbody(
                fh.Tr(
                    fh.Td("Raw Ruff Issues per kLOC", style="text-align: left"),
                    fh.Td(f"{row.violations_per_kloc.score:.0f}", style="text-align: center;"),
                    fh.Td(
                        f"{row.violations_per_kloc.grade}",
                        style="text-align: center; "
                        "color: var(--pico-muted-color); "
                        f"background-color: {row.violations_per_kloc.color}",
                    ),
                ),
                fh.Tr(
                    fh.Td("Weighted Ruff Issues per kLOC", style="text-align: left"),
                    fh.Td(f"{row.weighted_violations_per_kloc.score:.0f}", style="text-align: center;"),
                    fh.Td(
                        f"{row.weighted_violations_per_kloc.grade}",
                        style="text-align: center; "
                        "color: var(--pico-muted-color); "
                        f"background-color: {row.weighted_violations_per_kloc.color}",
                    ),
                ),
            ),
        ),
    )


def ruff_h(args: Namespace, project: Project, scan: Scan = None):
    # Create Pygal chart
    _, rows, _ = query(args, ReportLevel.HISTORY, project=project)

    style = Style(**DEFAULT_CHART_STYLE)

    chart = DateTimeLine(
        y_title="Ruff Issues",
        dots_size=1,
        height=500,
        show_legend=False,
        style=style,
        tooltip_border_radius=10,
        x_label_rotation=45,  # Angle labels to prevent overlap
        x_labels_major_every=2,  # Show every 5th label
        x_value_formatter=lambda dt: dt.strftime("%Y-%m-%d %H:%M"),
    )
    datetime_values = [(datetime.fromisoformat(ts_), count) for ts_, count in rows.items()]

    chart.add("-count-", datetime_values)

    return chart.render()  # Render as SVG and return bytes
