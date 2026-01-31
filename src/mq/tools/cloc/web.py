"""Web rendering obo 'cloc' tool."""

from argparse import Namespace
from datetime import datetime

from fasthtml import common as fh
from pygal import Bar, DateTimeLine
from pygal.style import Style

from mq.tools.base import Project, Scan
from mq.tools.cloc.models import query
from mq.utils.scoring import find_grade, get_nested_config
from mq.web import DEFAULT_CHART_STYLE, render_project_selector
from mq.web.page import render_page


# Page layout...
def render(request, name, config):
    """Do the primary page layout for this tools display page."""
    return render_page(
        request,
        name.title(),
        name,
        *render_project_selector(request, "/partials/set_project/cloc"),
        fh.Div(id="page-body-content"),
    )


def render_content(args: Namespace, request, s_project_id: str = None, analysis: str = None):
    """Render the content portion (ie. body) of the page."""
    return (
        *_render_current(args, request, s_project_id, analysis),
        *_render_history(args, request, s_project_id, analysis),
    )


def _render_current(args: Namespace, request, s_project_id: str = None, analysis: str = None):
    """Render the current status."""
    if not s_project_id:
        return fh.Section()
    project = Project.get(Project.id == int(s_project_id))
    scan = Scan.get_most_recent(project, "cloc", "cloc")

    chart_file_sizes = cloc_f(args, scan)

    return fh.Section(
        fh.H1("Current Status ", fh.Small(f"As Of {scan.as_of_display(collapse_today=True)}")),
        fh.Details(fh.Summary("Summary"), name="details", open=True, *cloc_0(args, scan)),
        fh.Details(fh.Summary("By Directory"), name="details", *cloc_1(args, scan)),
        fh.Details(fh.Summary("By File"), name="details", *cloc_2(args, scan)),
        fh.Details(fh.Summary("Derived"), name="details", *cloc_d(args, project, scan)),
        fh.Details(
            fh.Summary("File Sizes"),
            fh.Section(fh.Div(fh.NotStr(chart_file_sizes.decode("utf-8"))), cls="bordered"),
            name="details",
        ),
        cls="bordered",
    )


def _render_history(args: Namespace, request, s_project_id: str = None, analysis: str = None):
    """Render any history."""
    if not s_project_id:
        return fh.Section()
    project = Project.get(Project.id == int(s_project_id))
    chart = cloc_h(args, project)

    return fh.Section(
        fh.H1("History", style="margin-top: 1rem;"),
        fh.Div(
            fh.NotStr(chart.decode("utf-8")),
            cls="bordered",
        ),
    )


def cloc_0(args: Namespace, scan: Scan, project: Project = None):
    results = query(args, "0", scan=scan)
    if not results.lines_total:
        return ()
    return (
        fh.Table(
            fh.Thead(
                fh.Tr(
                    fh.Th(
                        "LOC",
                        scope="col",
                        style="text-align: center",
                    ),
                    fh.Th(
                        "Comments",
                        scope="col",
                        style="text-align: center",
                    ),
                    fh.Th(
                        "Blanks",
                        scope="col",
                        style="text-align: center",
                    ),
                    fh.Th(
                        "TOTAL",
                        scope="col",
                        style="text-align: center",
                    ),
                ),
            ),
            fh.Tbody(
                fh.Tr(
                    fh.Td(
                        f"{results.lines_code:,d}",
                        " ",
                        fh.Small(f"({results.lines_code_p:.1f}%)"),
                        style="text-align: right",
                    ),
                    fh.Td(
                        f"{results.lines_comment:,d}",
                        " ",
                        fh.Small(f"({results.lines_comment_p:.1f}%)"),
                        style="text-align: right",
                    ),
                    fh.Td(
                        f"{results.lines_blank:,d}",
                        " ",
                        fh.Small(f"({results.lines_blank_p:.1f}%)"),
                        style="text-align: right",
                    ),
                    fh.Td(
                        fh.B(f"{results.lines_total:,d}"),
                        style="text-align: right",
                    ),
                ),
            ),
        ),
    )


def cloc_1(args: Namespace, scan: Scan, project: Project = None):
    grand_total = query(args, "0", scan=scan)
    detail_rows = query(args, "1", scan=scan)

    t_head = fh.Tr(
        fh.Th("Directory", scope="col", style="text-align: left"),
        fh.Th("LOC", scope="col", style="text-align: right"),
        fh.Th("Comments", scope="col", style="text-align: right"),
        fh.Th("Blanks", scope="col", style="text-align: right"),
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


def cloc_2(args: Namespace, scan: Scan, project: Project = None):
    results, column_totals, grand_total = query(args, "2", scan=scan)

    t_head = fh.Tr(
        fh.Th("File", scope="col", style="text-align: left"),
        fh.Th("LOC", scope="col", style="text-align: right"),
        fh.Th("Comments", scope="col", style="text-align: right"),
        fh.Th("Blanks", scope="col", style="text-align: right"),
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
        fh.Td(f"{column_totals['lines_code']:.0f}", style="text-align: right"),
        fh.Td(f"{column_totals['lines_comment']:.0f}", style="text-align: right"),
        fh.Td(f"{column_totals['lines_blank']:.0f}", style="text-align: right"),
        fh.Td(f"{grand_total:.0f}", style="text-align: right"),
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


def cloc_d(args: Namespace, project: Project, scan: Scan):
    row = query(args, "d", scan=scan)
    return (
        fh.Table(
            fh.Thead(
                fh.Tr(
                    fh.Th("Metric", scope="col", style="text-align: left"),
                    fh.Th("Value", scope="col", style="text-align: center"),
                    fh.Th("Grade", scope="col", style="text-align: center"),
                    fh.Th(fh.Small("Explanation"), scope="col", style="text-align: left;"),
                ),
            ),
            fh.Tbody(
                fh.Tr(
                    fh.Td("File Density", style="text-align: left"),
                    fh.Td(f"{row.avg_lines_per_file.score:.0f}", style="text-align: center;"),
                    fh.Td(
                        f"{row.avg_lines_per_file.grade}",
                        style="text-align: center; "
                        "color: var(--pico-muted-color); "
                        f"background-color: {row.avg_lines_per_file.color}",
                    ),
                    fh.Td(fh.Small("Average LoC per File"), style="text-align: left;"),
                ),
                fh.Tr(
                    fh.Td("Code Density", style="text-align: left"),
                    fh.Td(f"{row.code_density.score:.0f}%", style="text-align: center;"),
                    fh.Td(
                        f"{row.code_density.grade}",
                        style="text-align: center; "
                        "color: var(--pico-muted-color); "
                        f"background-color: {row.code_density.color}",
                    ),
                    fh.Td(fh.Small("LOC / (LOC + Blanks)"), style="text-align: left;"),
                ),
                fh.Tr(
                    fh.Td("Comment Ratio", style="text-align: left"),
                    fh.Td(f"{row.comment_ratio.score:.0f}%", style="text-align: center;"),
                    fh.Td(
                        f"{row.comment_ratio.grade}",
                        style="text-align: center; "
                        "color: var(--pico-muted-color); "
                        f"background-color: {row.comment_ratio.color}",
                    ),
                    fh.Td(fh.Small("Comments / (Comment + LOC)"), style="text-align: left;"),
                ),
            ),
        ),
    )


def cloc_f(args: Namespace, scan: Scan, project: Project = None):
    # Get bucket definitions from configuration for coloring
    buckets = get_nested_config(args.config, "tools.cloc.histogram_file_size.buckets")

    histogram = query(args, "f", scan=scan)

    # Values to chart are a combination of the respective value AND the color
    # (which is based on the configurable bucket definitions)
    chart_entries = []
    for bucket_label, count in histogram:  # e.g. (("100-199", 23), ("200+", 3))
        try:
            (lookup, _) = bucket_label.split("-")
        except ValueError:
            lookup = bucket_label.replace("+", "")

        _, color = find_grade(float(lookup), buckets)
        chart_entries.append(dict(value=count, color=color))

    chart = Bar(
        height=400,
        show_legend=False,
        style=Style(**DEFAULT_CHART_STYLE),
        title=None,
        tooltip_border_radius=10,
        y_title="Percent of Files by Total Lines",
        x_labels=[label for label, _ in histogram],
        value_formatter=lambda x: f"{x:.0f}%",  # Y-axis labels
        formatter=lambda x: f"{x:.1f}%",  # Tooltips when hovering
    )
    chart.add("File Size", chart_entries)

    return chart.render()


def cloc_h(args: Namespace, project: Project, scan: Scan = None):
    # Create Pygal chart
    _, rows, _, _, _, _ = query(args, "h", project=project)

    style = Style(**DEFAULT_CHART_STYLE)

    chart = DateTimeLine(
        dots_size=1,
        height=500,
        legend_at_bottom=True,
        legend_at_bottom_columns=3,
        style=style,
        tooltip_border_radius=10,
        x_label_rotation=45,  # Angle labels to prevent overlap
        x_labels_major_every=2,  # Show every 5th label
        x_value_formatter=lambda dt: dt.strftime("%Y-%m-%d %H:%M"),
        y_title="Lines",
    )
    datetime_values_cd = [(datetime.fromisoformat(row.timestamp), row.total_code) for row in rows]
    datetime_values_cm = [(datetime.fromisoformat(row.timestamp), row.total_comment) for row in rows]
    datetime_values_bl = [(datetime.fromisoformat(row.timestamp), row.total_blank) for row in rows]

    chart.add("LOC", datetime_values_cd)
    chart.add("Comments", datetime_values_cm)
    chart.add("Blanks", datetime_values_bl)

    return chart.render()  # Render as SVG and return bytes
