"""Render web data obo running 'ty' tool."""

import logging
from argparse import Namespace
from datetime import datetime
from types import SimpleNamespace as Sns

import plotly.graph_objects as go
from bottle import request

from qyx.tools.base import Project, Scan, State
from qyx.tools.ty.models import query_0, query_1, query_2, query_3, query_h
from qyx.web.page import generic_render, generic_render_scans, render_partial
from qyx.web.plotly import SERIES_COLORS, custom_labels, style_figure


log = logging.getLogger(__name__)


################################################################################################
# Page layout...
################################################################################################
def render(template: str = "ty::page.html") -> str:
    """Render the primary page layout for this tools display page."""
    return generic_render("ty", template, get_content)


def render_scans(template: str = "base::_select_scan.cascading.html") -> str:
    """Render the scan select widget based on a new project selection."""
    return generic_render_scans("ty")


def render_content(template: str = "ty::body.htmx") -> str:
    """Render the content portion (ie. body) of the page."""
    s_scan_id = request.query.scan
    scan = Scan.get_or_none(Scan.id == int(s_scan_id)) if s_scan_id else None
    if not scan:
        return render_partial("base::_no_scans_yet.htmx")
    context = get_content(scan)
    return render_partial(template, **context.__dict__)


################################################################################################
def get_content(scan: Scan) -> Sns:
    """Populate our tool's home page to the specified scan."""
    args = request.app.args

    State.update(args, project=scan.request.project.name, analysis="ty")

    context = Sns()
    context.ty_as_of = scan.as_of_display(collapse_today=True)
    context.ty_0 = query_0(args, scan)
    context.ty_1 = query_1(scan)
    context.ty_2 = query_2(scan)
    context.ty_3 = query_3(scan)
    context.ty_h = ty_h(args, scan)
    return context


################################################################################################
def ty_h(args: Namespace, project: Project):
    """Render the history chart of number of issues over time."""
    result = query_h(project)
    if not result.transposed:
        return None

    x_values = [datetime.fromisoformat(ts_) for ts_ in result.transposed.keys()]
    y_values = list(result.transposed.values())

    # Create custom hover labels
    s_y_values = []
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
