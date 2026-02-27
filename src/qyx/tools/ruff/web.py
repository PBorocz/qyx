"""Render web data obo running 'ruff' tool."""

from argparse import Namespace
from datetime import datetime

import plotly.graph_objects as go
from bottle import request

from qyx.tools.base import Project, Scan, State
from qyx.tools.ruff.models import query_0, query_1, query_2, query_h
from qyx.web import get_project_selector
from qyx.web.page import render_page, render_partial
from qyx.web.plotly import SERIES_COLORS, custom_labels, style_figure


################################################################################################
# Page layout...
################################################################################################
def render(template: str = "ruff::page.html") -> str:
    """Render the primary page layout for this tools display page."""
    project_options = get_project_selector("ruff")
    return render_page(
        "QYX-RUFF",
        template,
        project_options=project_options,
        set_project="/partials/set_project/ruff",
    )


################################################################################################
def render_content(template: str = "ruff::body.htmx") -> str:
    """Render the content portion (ie. body) of the page."""
    args = request.app.args

    s_project_id = request.query.project
    project = Project.get_or_none(Project.id == int(s_project_id)) if s_project_id else None
    if not project:
        return render_partial("base::fragments/_no_project_yet.htmx")

    scan = Scan.get_most_recent(project, "ruff", "ruff")
    if not scan:
        return render_partial("base::fragments/_no_scans_yet.htmx")

    State.update(args, project=project.name, analysis="ruff")

    # fmt: off
    context = Namespace()
    context.ruff_as_of = scan.as_of_display(collapse_today=True)
    context.ruff_0 = query_0(args, project, scan)
    context.ruff_1 = query_1(scan)
    context.ruff_2 = query_2(scan)
    context.ruff_h =  ruff_h(args, project, scan)
    # fmt: on
    return render_partial(template, **context.__dict__)


def ruff_h(args: Namespace, project: Project, scan: Scan):
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
