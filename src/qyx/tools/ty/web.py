"""Render web data obo running 'ty' tool."""

from argparse import Namespace
from datetime import datetime
from types import SimpleNamespace as Sns

import plotly.graph_objects as go
from bottle import request

from qyx.tools._models_ import Project, Scan, State
from qyx.tools.ty.models import query_ty_0, query_ty_1, query_ty_2, query_ty_3, query_ty_h
from qyx.web.page import render, render_content
from qyx.web.plotly import SERIES_COLORS, custom_labels, style_figure


################################################################################################
# Routing/View methods
################################################################################################
def view(template: str = "ty::page.html") -> str:
    """View callback to render the entire tool page: project selector, analysis selector and body content."""
    o_tool = request.app.args.tools["ty"]
    return render(o_tool, template, get_content)


def view_content() -> str:
    """View callback for when a new analysis is selected, just need to update the body content directly."""
    o_tool = request.app.args.tools["ty"]
    project: str = request.query.project
    return render_content(project, o_tool, "ty", get_content)


################################################################################################
def get_content(scan: Scan) -> Sns:
    """Populate our tool's home page to the specified scan."""
    args = request.app.args

    State.update(args, project=scan.request.project.name, analysis=scan.analysis)

    context = Sns()
    context.ty_as_of = scan.as_of_display(collapse_today=True)
    context.ty_0 = query_ty_0(args, scan)
    context.ty_1 = query_ty_1(scan)
    context.ty_2 = query_ty_2(scan)
    context.ty_3 = query_ty_3(scan)
    context.ty_h = view_ty_h(args, scan.request.project)
    return context


################################################################################################
def view_ty_h(args: Namespace, project: Project):
    """Render the history chart of number of issues over time."""
    result = query_ty_h(project)
    if not result.transposed:
        return None

    x_values = [datetime.fromisoformat(ts_) for ts_ in result.transposed.keys()]
    y_values: list[int] = list(result.transposed.values())

    # Create custom hover labels
    s_y_values: list[str] = []
    for count in y_values:
        match count:
            case 0:
                s_y_values.append("No Ty Issues!")
            case 1:
                s_y_values.append(f"{count} Ty Issue")
            case _:
                s_y_values.append(f"{count} Ty Issues")
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
            "yaxis_title": "Ty Issues",
        },
    )

    return fig.to_html()
