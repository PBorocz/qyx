"""Render web data obo running 'ty' tool."""

from argparse import Namespace
from datetime import datetime

import plotly.graph_objects as go
from bottle import request

from qyx.constants import ReportLevel as Rl
from qyx.tools.base import Project, Scan, State
from qyx.tools.ty.models import query
from qyx.web import get_project_selector
from qyx.web.page import render_page, render_partial
from qyx.web.plotly import SERIES_COLORS, custom_labels, style_figure


################################################################################################
# Page layout...
################################################################################################
def render(template: str = "ty::pages/main.html") -> str:
    """Render the primary page layout for this tools display page."""
    project_options = get_project_selector()
    return render_page(
        "QYX-TY",
        template,
        project_options=project_options,
        set_project="/partials/set_project/ty",
    )


################################################################################################
def render_content(template: str = "ty::fragments/body.html") -> str:
    """Render the content portion (ie. body) of the page."""
    args = request.app.args

    s_project_id = request.query.project
    project = Project.get_or_none(Project.id == int(s_project_id)) if s_project_id else None
    if not project:
        return render_partial("base::fragments/_no_project_yet.html")

    scan = Scan.get_most_recent(project, "ty", "ty")
    if not scan:
        return render_partial("base::fragments/_no_scans_yet.html")

    State.update(args, project=project.name, analysis="ty")

    # fmt: off
    context = Namespace()
    context.ty_as_of = scan.as_of_display(collapse_today=True)
    context.ty_0 = ty_0(args, project, scan)
    context.ty_1 = ty_1(args, project, scan)
    context.ty_2 = ty_2(args, project, scan)
    context.ty_3 = ty_3(args, project, scan)
    context.ty_d = ty_d(args, project, scan)
    context.ty_h = ty_h(args, project, scan)
    # fmt: on
    return render_partial(template, **context.__dict__)


def ty_0(args: Namespace, project: Project, scan: Scan):
    return dict(row=query(args, Rl.SUMMARY, scan=scan))


def ty_1(args: Namespace, project: Project, scan: Scan):
    summary = query(args, Rl.SUMMARY, scan=scan)
    results = query(args, Rl.DIRECTORY, scan=scan)
    return dict(summary=summary, results=results)


def ty_2(args: Namespace, project: Project, scan: Scan):
    return dict(rows=query(args, Rl.FILE, scan=scan))


def ty_3(args: Namespace, project: Project, scan: Scan):
    return dict(rows=query(args, Rl.GRANULAR, scan=scan))


def ty_d(args: Namespace, project: Project, scan: Scan):
    """Report on derived ty metrics."""
    return dict(row=query(args, Rl.DERIVED, project=project, scan=scan))


def ty_h(args: Namespace, project: Project, scan: Scan):
    """Render the history chart of number of issues over time."""
    _, messages, rows, _ = query(args, Rl.HISTORY, project=project)
    if not rows:
        return None

    x_values = [datetime.fromisoformat(ts_) for ts_ in rows.keys()]
    y_values = list(rows.values())

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
            "yaxis_title": "Ty Issues",
        },
    )

    return fig.to_html()
