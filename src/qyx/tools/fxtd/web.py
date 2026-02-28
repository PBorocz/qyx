"""Render web data obo running 'fxtd' tool."""

from argparse import Namespace
from datetime import datetime
from types import SimpleNamespace as Sns

import plotly.graph_objects as go
from bottle import request

from qyx.tools.base import Project, Scan, State
from qyx.tools.fxtd.models import query_0, query_1, query_2, query_h
from qyx.web.page import generic_render, generic_render_scans, render_partial
from qyx.web.plotly import SERIES_COLORS, custom_labels, style_figure


################################################################################################
# Page layout...
################################################################################################
def render(template: str = "fxtd::page.html") -> str:
    """Render the primary page layout for this tools display page."""
    return generic_render("fxtd", template, get_content)


def render_scans(template: str = "base::_select_scan.cascading.html") -> str:
    """Render the scan select widget based on a new project selection."""
    return generic_render_scans("fxtd")


def render_content(template: str = "fxtd::body.htmx") -> str:
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

    State.update(args, project=scan.request.project.name, analysis="fxtd")

    context = Namespace()
    context.fxtd_as_of = scan.as_of_display(collapse_today=True)
    context.fxtd_0 = query_0(args, scan)
    context.fxtd_1 = query_1(scan)
    context.fxtd_2 = query_2(scan)
    context.fxtd_h = fxtd_h(args, scan.request.project)
    return context


################################################################################################
def fxtd_h(args: Namespace, project: Project) -> bytes | None:
    result = query_h(project)
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
