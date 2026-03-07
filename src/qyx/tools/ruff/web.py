"""Render web data obo running 'ruff' tool."""

from argparse import Namespace
from datetime import datetime
from types import SimpleNamespace as Sns

import plotly.graph_objects as go
from bottle import request

from qyx.tools.base import Project, Scan, State
from qyx.tools.ruff.models import query_ruff_0, query_ruff_1, query_ruff_2, query_ruff_h
from qyx.web.page import render, render_content
from qyx.web.plotly import SERIES_COLORS, custom_labels, style_figure


################################################################################################
# Routing/View methods
################################################################################################
def view(template: str = "ruff::page.html") -> str:
    """View callback to render the entire tool page: project selector, analysis selector and body content."""
    o_tool = request.app.args.tools["ruff"]
    return render(o_tool, template, get_content)


def view_content() -> str:
    """View callback for when a new analysis is selected, just need to update the body content directly."""
    o_tool = request.app.args.tools["ruff"]
    project: str = request.query.project
    return render_content(project, o_tool, "ruff", get_content)


################################################################################################
def get_content(scan: Scan) -> str:
    """Render the content portion (ie. body) of the page."""
    args = request.app.args

    State.update(args, project=scan.request.project.name, analysis=scan.analysis)

    context = Sns()
    context.ruff_as_of = scan.as_of_display(collapse_today=True)
    context.ruff_0 = query_ruff_0(args, scan)
    context.ruff_1 = query_ruff_1(scan)
    context.ruff_2 = query_ruff_2(scan)
    context.ruff_h = view_ruff_h(args, scan.request.project)
    return context


################################################################################################
def view_ruff_h(args: Namespace, project: Project):
    """Render the history chart of number of issues over time."""
    result = query_ruff_h(project)
    if not result.transposed:
        return None

    x_values = [datetime.fromisoformat(ts_) for ts_ in result.transposed.keys()]
    y_values = list(result.transposed.values())

    # Create custom hover labels
    s_y_values = []
    for count in y_values:
        match count:
            case 0:
                s_y_values.append("No Ruff Issues!")
            case 1:
                s_y_values.append(f"{count} Ruff Issue")
            case _:
                s_y_values.append(f"{count} Ruff Issues")
    labels = custom_labels("", result.messages, x_values, s_y_values)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=y_values,
            mode="lines+markers",
            marker_color=SERIES_COLORS[0],
            line_color=SERIES_COLORS[0],
            customdata=labels,
            hovertemplate="%{customdata}",
        ),
    )

    style_figure(
        fig,
        layout={
            "yaxis_title": "Ruff Issues",
        },
    )

    return fig.to_html()
