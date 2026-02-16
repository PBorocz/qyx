"""MI - Level 0."""

from argparse import Namespace
from datetime import datetime

import plotly.graph_objects as go

from qyx.constants import ReportLevel
from qyx.tools.base import Project, Scan
from qyx.tools.radon.models import query_mi
from qyx.web.plotly import SERIES_COLORS, custom_labels, style_figure


def mi_0(args: Namespace, project: Project, scan: Scan) -> dict[str, float | None]:
    return dict(metric=query_mi(args, ReportLevel.SUMMARY, scan=scan))


def mi_1(args: Namespace, project: Project, scan: Scan):
    return dict(rows=query_mi(args, ReportLevel.DIRECTORY, scan)[1])


def mi_2(args: Namespace, project: Project, scan: Scan):
    return dict(rows=query_mi(args, ReportLevel.FILE, scan)[1])


def mi_d(args: Namespace, project: Project, scan: Scan):
    return dict(row=query_mi(args, ReportLevel.DERIVED, project=project, scan=scan))


def mi_h(args: Namespace, project: Project, scan: Scan):
    """Render the maintainability index chart."""
    messages, rows, roc = query_mi(args, ReportLevel.HISTORY, project=project, last=None)
    x_values = [datetime.fromisoformat(ts_) for ts_ in rows.keys()]
    y_values = [round(value, 2) for value in rows.values()]
    labels = custom_labels("", messages, x_values, y_values)
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
            "yaxis_title": "Maintainability Index",
        },
    )
    return fig.to_html()
