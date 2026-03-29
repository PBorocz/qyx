"""Web rendering obo 'scc' tool."""

import logging
from argparse import Namespace
from datetime import datetime
from types import SimpleNamespace as Sns

from bottle import request
import plotly.graph_objects as go

from qyx.tools._models_ import Project, Scan, State
from qyx.tools.scc.models import query_scc_0, query_scc_1, query_scc_2, query_scc_h
from qyx.web.page import render, render_dimensions, render_content
from qyx.web.plotly import SERIES_COLORS, custom_labels, style_figure

log = logging.getLogger(__name__)


################################################################################################
# Routing/View methods
################################################################################################
def view(template: str = "scc::page.html") -> str:
    """View callback to render the entire tool page: project selector, dimension selector and body content."""
    o_tool = request.app.args.tools["scc"]
    return render(o_tool, template, get_content)


def view_dimension() -> str:
    """View callback when project changes: Render BOTH updated dimension selector *AND* fresh body on an OOB basis."""
    o_tool = request.app.args.tools["scc"]
    project: str = request.query.project
    return render_dimensions(o_tool, project, get_content)


def view_content() -> str:
    """View callback for when a new dimension is selected, just need to update the body content directly."""
    o_tool = request.app.args.tools["scc"]
    project: str = request.query.project
    log.debug(f"view_content: {request.query.dimension=}")
    return render_content(project, o_tool, request.query.dimension, get_content)


################################################################################################
def get_content(scan: Scan, dimension: str) -> Sns:
    """Populate our tool's home page to the specified scan for the specified dimension."""
    args = request.app.args
    log.debug(f"{scan=} {dimension=} ")

    State.update(args, project=scan.request.project.name, dimension=dimension)

    context = Sns()
    context.scc_as_of = scan.as_of_display(collapse_today=True)
    context.scc_0 = query_scc_0(args, scan, dimension)
    context.scc_1 = query_scc_1(args, scan, dimension)
    context.scc_2 = query_scc_2(args, scan, dimension)
    context.scc_h = view_scc_h(args, scan.request.project, dimension)
    return context


def view_scc_h(args: Namespace, project: Project, dimension: str) -> bytes | None:
    result = query_scc_h(project, dimension)
    if not result.rows:
        return None

    metric_titles = (
        ("code", f"{dimension.title()}: Lines of Code"),
        ("uloc", "Lines of Unique Code"),
        ("comment", "Comments"),
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
