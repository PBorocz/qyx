"""Render web data obo running 'fxtd' tool."""

from argparse import Namespace
from datetime import datetime

import plotly.graph_objects as go
from bottle import request

from qyx.tools.base import Project, Scan, State
from qyx.tools.fxtd.models import query_0, query_1, query_2, query_h
from qyx.web import get_project_selector
from qyx.web.page import render_page, render_partial
from qyx.web.plotly import SERIES_COLORS, custom_labels, style_figure


################################################################################################
# Page layout...
################################################################################################
def render(template: str = "fxtd::page.html") -> str:
    """Render the primary page layout for this tools display page."""
    project_options = get_project_selector()
    return render_page(
        "QYX-FXTD",
        template,
        project_options=project_options,
        set_project="/partials/set_project/fxtd",
    )


################################################################################################
def render_content(template: str = "fxtd::body.htmx") -> str:
    """Render the content portion (ie. body) of the page."""
    args = request.app.args
    s_project_id = request.query.project
    project = Project.get(Project.id == int(s_project_id))
    if not s_project_id or not project:
        return render_partial("base::fragments/_no_project_yet.html")

    scan = Scan.get_most_recent(project, "fxtd", "fxtd")
    if not (project and scan):
        return render_partial("base::fragments/_no_scans_yet.html")

    State.update(args, project=project.name, analysis="fxtd")

    # fmt: off
    context = Namespace()
    context.fxtd_as_of = scan.as_of_display(collapse_today=True)
    context.fxtd_0 = query_0(args, project, scan)
    context.fxtd_1 = query_1(scan)
    context.fxtd_2 = query_2(scan)
    context.fxtd_h = fxtd_h(args, project)
    # fmt: on
    return render_partial(template, **context.__dict__)


def fxtd_h(args: Namespace, project: Project) -> bytes | None:
    timestamps, messages, transposed, rocs = query_h(project)
    if not transposed:
        return None

    fig = go.Figure()
    for i, metric in enumerate(list(transposed.keys())):
        dt_values = transposed[metric]
        x_values = [datetime.fromisoformat(ts_) for ts_ in dt_values.keys()]
        y_values = list(dt_values.values())

        # We want custom hover labels based on the respective git messages
        labels = custom_labels(metric, messages, x_values, y_values)

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
