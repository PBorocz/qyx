"""Render web data obo running 'ruff' tool."""

from argparse import Namespace
from datetime import datetime

import plotly.graph_objects as go
from bottle import request

from qyx.constants import ReportLevel
from qyx.tools.base import Project, Scan, State
from qyx.tools.ruff.models import query
from qyx.web import get_project_selector
from qyx.web.page import render_page, render_partial
from qyx.web.plotly import SERIES_COLORS, custom_labels, style_figure


################################################################################################
# Page layout...
################################################################################################
def render(template: str = "ruff::pages/main.html") -> str:
    """Render the primary page layout for this tools display page."""
    project_options = get_project_selector()
    return render_page(
        "QYX-RUFF",
        template,
        project_options=project_options,
        set_project="/partials/set_project/ruff",
    )


################################################################################################
def render_content(template: str = "ruff::fragments/body.html") -> str:
    """Render the content portion (ie. body) of the page."""
    args = request.app.args
    s_project_id = request.query.project
    if not s_project_id:
        render_partial(template)

    project = Project.get(Project.id == int(s_project_id))
    scan = Scan.get_most_recent(project, "ruff", "ruff")
    if not (project and scan):
        render_partial(template)

    State.update(args, project=project.name, analysis="ruff")

    # fmt: off
    context = Namespace()
    context.as_of   = scan.as_of_display(collapse_today=True)
    context.ruff_0  = ruff_0(args, scan)
    context.ruff_1  = ruff_1(args, scan)
    context.ruff_2  = ruff_2(args, scan)
    context.ruff_d  = ruff_d(args, scan, project)
    context.chart_t = ruff_h(args, project)
    # fmt: on
    return render_partial(template, **context.__dict__)


def ruff_0(args: Namespace, scan: Scan, **kwargs):
    return dict(row=query(args, ReportLevel.SUMMARY, scan=scan))


def ruff_1(args: Namespace, scan: Scan, project: Project = None):
    summary = query(args, ReportLevel.SUMMARY, scan=scan)
    results = query(args, ReportLevel.DIRECTORY, scan=scan)
    return dict(summary=summary, results=results)


def ruff_2(args: Namespace, scan: Scan, project: Project = None):
    return dict(rows=query(args, ReportLevel.FILE, scan=scan))


def ruff_d(args: Namespace, scan: Scan, project: Project):
    """Report on derived ruff metrics."""
    return dict(row=query(args, ReportLevel.DERIVED, project=project, scan=scan))


def ruff_h(args: Namespace, project: Project, scan: Scan = None):
    """Render the history chart of number of issues over time."""
    _, messages, rows, _ = query(args, ReportLevel.HISTORY, project=project)
    if not rows:
        return None

    x_values = [datetime.fromisoformat(ts_) for ts_ in rows.keys()]
    y_values = list(rows.values())

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
    labels = custom_labels("", messages, x_values, s_y_values)

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
