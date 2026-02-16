"""Web rendering obo 'cloc' tool."""

from argparse import Namespace
from datetime import datetime

import plotly.graph_objects as go
from bottle import request

from qyx.constants import ReportLevel
from qyx.tools.base import Project, Scan, State
from qyx.tools.cloc.models import query
from qyx.utils.scoring import find_grade
from qyx.web import get_project_selector
from qyx.web.page import render_page, render_partial
from qyx.web.plotly import SERIES_COLORS, custom_labels, style_figure


def render(template: str = "cloc::pages/main.html") -> str:
    """Render the tool's primary page."""
    project_options = get_project_selector()
    return render_page(
        "QYX-CLOC",
        template,
        project_options=project_options,
        set_project="/partials/set_project/cloc",
    )


def render_content(template: str = "cloc::fragments/body.html"):
    """Render the content portion (ie. body) of the page."""
    args = request.app.args
    s_project_id = request.query.project
    if not s_project_id:
        # FIXME: Make this use the template that notifies of an empty project
        render_partial(template)

    project = Project.get(Project.id == int(s_project_id))
    scan = Scan.get_most_recent(project, "cloc", "cloc")
    if not (project and scan):
        render_partial(template)

    State.update(args, project=project.name, analysis="cloc")

    # fmt: off
    context = Namespace()
    context.as_of   = scan.as_of_display(collapse_today=True)
    context.level_0 = query(args, ReportLevel.SUMMARY, scan=scan)
    context.level_1 = cloc_1(args, scan)
    context.level_2 = cloc_2(args, scan)
    context.level_d = cloc_d(args, scan, project)
    context.chart_f = cloc_f(args, scan)
    context.chart_h = cloc_h(args, project)
    # fmt: on
    return render_partial(template, **context.__dict__)


def cloc_1(args: Namespace, scan: Scan, project: Project = None):
    return dict(
        grand_total=query(args, ReportLevel.SUMMARY, scan=scan),
        detail_rows=query(args, ReportLevel.DIRECTORY, scan=scan),
    )


def cloc_2(args: Namespace, scan: Scan, project: Project = None):
    results, column_totals, grand_total = query(args, ReportLevel.FILE, scan=scan)
    return dict(results=results, column_totals=column_totals, grand_total=grand_total)


def cloc_d(args: Namespace, scan: Scan, project: Project):
    return dict(row=query(args, ReportLevel.DERIVED, scan=scan))


def cloc_f(args: Namespace, scan: Scan):
    # Get bucket definitions from configuration for coloring
    buckets = args.config.get("tools.cloc.histogram_file_size.buckets")
    histogram = query(args, "f", scan=scan)

    # Values to chart are a combination of the respective value AND the color
    # (which is based on the configurable bucket definitions)
    chart_entries = []
    for bucket_label, count in histogram:  # e.g. (("100-199", 23.5), ("200+", 30.4))
        try:
            (lookup, _) = bucket_label.split("-")
        except ValueError:
            lookup = bucket_label.replace("+", "")

        _, color = find_grade(float(lookup), buckets)
        chart_entries.append(dict(value=int(count), color=color))

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=[label for label, _ in histogram],
            y=[entry["value"] for entry in chart_entries],
            marker_color=[entry["color"] for entry in chart_entries],
            hovertemplate="%{y}% " + "of files are <b>%{x}</b> lines long<br>" + "<extra></extra>",
        ),
    )

    style_figure(
        fig,
        layout={
            "xaxis": None,
            "yaxis_title": "Percent of Files by Total Lines",
        },
    )
    return fig.to_html()


def cloc_h(args: Namespace, project: Project, scan: Scan = None) -> bytes | None:
    _, messages, rows, _, _, _, _ = query(args, ReportLevel.HISTORY, project=project)
    if not rows:
        return None

    metric_titles = (
        ("total_code", "Total Code Lines"),
        ("total_comment", "Total Comment Lines"),
        ("total_blank", "Total Blank Lines"),
    )
    fig = go.Figure()
    for i, (metric, title) in enumerate(metric_titles):
        x_values = [datetime.fromisoformat(row.timestamp) for row in rows]
        y_values = [getattr(row, metric) for row in rows]

        # We want custom hover labels based on the respective git messages
        labels = custom_labels(title, messages, x_values, y_values)

        # Add a series for each specific metric
        fig.add_trace(
            go.Scatter(
                x=x_values,
                y=y_values,
                mode="lines+markers",
                name=title,
                marker=dict(color=SERIES_COLORS[i % len(SERIES_COLORS)], size=4, opacity=0.5),
                line=dict(color=SERIES_COLORS[i % len(SERIES_COLORS)], width=2),
                customdata=labels,
                hovertemplate="%{customdata}",
            ),
        )

    style_figure(fig, layout={"yaxis_title": "Lines"})

    return fig.to_html()
