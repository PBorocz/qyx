"""Render web data obo running 'fxtd' tool."""

from argparse import Namespace
from datetime import datetime
from types import SimpleNamespace as Sns

import plotly.graph_objects as go
from bottle import request

from qyx.tools._models_ import Project, Scan, State
from qyx.tools.fxtd.models import query_fxtd_0, query_fxtd_1, query_fxtd_2, query_fxtd_h
from qyx.web.page import render, render_content
from qyx.web.plotly import SERIES_COLORS, custom_labels, style_figure


################################################################################################
# Routing/View methods
################################################################################################
def view(template: str = "fxtd::page.html") -> str:
    """View callback to render the entire tool page: project selector, dimension selector and body content."""
    o_tool = request.app.args.tools["fxtd"]
    return render(o_tool, template, get_content)


def view_content() -> str:
    """View callback for when a new dimension is selected, just need to update the body content directly."""
    o_tool = request.app.args.tools["fxtd"]
    project: str = request.query.project
    return render_content(project, o_tool, "fxtd", get_content)


################################################################################################
def get_content(scan: Scan, *args) -> Sns:
    """Populate our tool's home page to the specified scan."""
    args = request.app.args

    State.update(args, project=scan.request.project.name)

    context = Sns()
    context.fxtd_as_of = scan.as_of_display(collapse_today=True)
    context.fxtd_0 = query_fxtd_0(args, scan)
    context.fxtd_1 = query_fxtd_1(scan)
    context.fxtd_2 = query_fxtd_2(scan)
    context.fxtd_h = view_fxtd_h(args, scan.request.project)
    return context


################################################################################################
def view_fxtd_h(args: Namespace, project: Project) -> bytes | None:
    result = query_fxtd_h(project)
    if not result.transposed:
        return None

    fig = go.Figure()
    for i, metric in enumerate(list(result.transposed.keys())):
        dt_values = result.transposed[metric]
        x_values = [datetime.fromisoformat(ts_) for ts_ in dt_values.keys()]
        y_values = list(dt_values.values())

        # We want custom hover labels based on the respective git messages
        labels = custom_labels(metric, result.messages, x_values, y_values)

        fig.add_trace(
            go.Scatter(
                line_color=SERIES_COLORS[i % len(SERIES_COLORS)],
                marker_color=SERIES_COLORS[i % len(SERIES_COLORS)],
                mode="lines+markers",
                name=f"{metric.title()}'s",
                x=x_values,
                y=y_values,
                customdata=labels,
                hovertemplate="%{customdata}",
            ),
        )

    style_figure(
        fig,
        layout={
            "yaxis_title": "Number of Instances",
        },
    )

    return fig.to_html()
