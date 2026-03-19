"""Web rendering obo 'cloc' tool."""

from argparse import Namespace
from datetime import datetime
from types import SimpleNamespace as Sns

import plotly.graph_objects as go
from bottle import request

from qyx.tools._models_ import Project, Scan, State
from qyx.tools.cloc.models import query_cloc_0, query_cloc_1, query_cloc_2, query_cloc_f, query_cloc_h
from qyx.utils.scoring import find_grade
from qyx.web.page import render, render_content
from qyx.web.plotly import SERIES_COLORS, custom_labels, style_figure


################################################################################################
# Routing/View methods
################################################################################################
def view(template: str = "cloc::page.html") -> str:
    """View callback to render the entire tool page: project selector and body content."""
    o_tool = request.app.args.tools["cloc"]
    return render(o_tool, template, get_content)


def view_content() -> str:
    """View callback for when a new project is selected, just need to update the body content directly."""
    o_tool = request.app.args.tools["cloc"]
    project: str = request.query.project
    return render_content(project=project, tool=o_tool, content_method=get_content)


################################################################################################
def get_content(scan: Scan, *args) -> Sns:
    """Populate our tool's home page to the specified scan."""
    args = request.app.args
    State.update(args, project=scan.request.project.name)

    context = Sns()
    context.cloc_as_of = scan.as_of_display(collapse_today=True)
    context.cloc_0 = query_cloc_0(args, scan)
    context.cloc_1 = query_cloc_1(args, scan)
    context.cloc_2 = query_cloc_2(args, scan)
    context.cloc_f = view_cloc_f(args, scan)
    context.cloc_h = view_cloc_h(args, scan.request.project)
    return context


def view_cloc_h(args: Namespace, project: Project) -> bytes | None:
    result = query_cloc_h(project)
    if not result.rows:
        return None

    metric_titles = (
        ("total_code", "Total Code Lines"),
        ("total_comment", "Total Comment Lines"),
        ("total_blank", "Total Blank Lines"),
    )
    fig = go.Figure()
    for i, (metric, title) in enumerate(metric_titles):
        x_values = [datetime.fromisoformat(row.timestamp) for row in result.rows]
        y_values = [getattr(row, metric) for row in result.rows]

        # We want custom hover labels based on the respective git messages
        labels = custom_labels(title, result.messages, x_values, y_values)

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


################################################################################################
def view_cloc_f(args: Namespace, scan: Scan):
    # Get bucket definitions from configuration for coloring
    buckets = args.config.get("tools.cloc.histogram_file_size.buckets")
    histogram = query_cloc_f(args, scan)

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
