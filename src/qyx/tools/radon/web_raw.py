"""Raw - Level 0."""

from argparse import Namespace
from datetime import datetime

import plotly.graph_objects as go

from qyx.constants import ReportLevel
from qyx.tools.base import Project, Scan
from qyx.tools.radon.models import query_raw
from qyx.web.plotly import SERIES_COLORS, custom_labels, style_figure


def raw_0(args: Namespace, project: Project, scan: Scan):
    return dict(row=query_raw(args, ReportLevel.SUMMARY, scan=scan))


def raw_1(args: Namespace, project: Project, scan: Scan):
    return dict(rows=query_raw(args, ReportLevel.DIRECTORY, scan)[0])


def raw_2(args: Namespace, project: Project, scan: Scan):
    return dict(rows=query_raw(args, ReportLevel.FILE, scan))


def raw_h(args: Namespace, project: Project, scan: Scan = None):
    """Create chart obo all Raw metrics."""
    _, messages, transposed, _, _ = query_raw(args, ReportLevel.HISTORY, project=project, last=None)

    fig = go.Figure()
    for i, (metric, dt_rows) in enumerate(list(transposed.items())):
        x_values = [datetime.fromisoformat(ts_) for ts_ in dt_rows.keys()]
        y_values = list(dt_rows.values())
        labels = custom_labels(metric.upper(), messages, x_values, y_values)
        fig.add_trace(
            go.Scatter(
                line_color=SERIES_COLORS[i % len(SERIES_COLORS)],
                marker_color=SERIES_COLORS[i % len(SERIES_COLORS)],
                mode="lines+markers",
                name=metric.upper(),
                x=x_values,
                y=y_values,
                customdata=labels,
                hovertemplate="%{customdata}",
            ),
        )

    style_figure(
        fig,
        layout={
            "yaxis_title": "Number of Lines",
        },
    )

    return fig.to_html()
