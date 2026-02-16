"""CC - Level 0."""

from argparse import Namespace
from datetime import datetime

import plotly.graph_objects as go

from qyx.constants import ReportLevel
from qyx.tools.base import Project, Scan
from qyx.tools.radon.models import RadonCc, query_cc
from qyx.web.plotly import SERIES_COLORS, custom_labels, style_figure


def cc_0(args: Namespace, project: Project, scan: Scan) -> dict:
    return dict(rows=query_cc(args, ReportLevel.SUMMARY, scan=scan))


def cc_1(args: Namespace, project: Project, scan: Scan) -> dict:
    return dict(rows=query_cc(args, ReportLevel.DIRECTORY, scan=scan))


def cc_2(args: Namespace, project: Project, scan: Scan) -> dict:
    return dict(rows=query_cc(args, ReportLevel.FILE, scan=scan))


def cc_3(args: Namespace, project: Project, scan: Scan) -> dict:
    return dict(rows=query_cc(args, ReportLevel.DETAIL, scan=scan))


def cc_d(args: Namespace, project: Project, scan: Scan) -> dict:
    return dict(rows=query_cc(args, ReportLevel.DERIVED, project=project, scan=scan))


def cc_h(args: Namespace, project: Project, scan: Scan) -> str:
    """Render our chart to display Radon CC information."""
    _, messages, transposed, _ = query_cc(args, ReportLevel.HISTORY, project=project, last=None)

    fig = go.Figure()
    for i, entity_type in enumerate(("C", "F", "M")):  # HARD-CODE!
        values_by_timestamp = transposed[entity_type]
        x_values = [datetime.fromisoformat(ts_) for ts_ in values_by_timestamp.keys()]
        y_values = [round(value, 2) for value in values_by_timestamp.values()]
        labels = custom_labels(f"({entity_type})", messages, x_values, y_values)
        fig.add_trace(
            go.Scatter(
                x=x_values,
                y=y_values,
                customdata=labels,
                hovertemplate="%{customdata}",
                line_color=SERIES_COLORS[i % len(SERIES_COLORS)],
                marker_color=SERIES_COLORS[i % len(SERIES_COLORS)],
                mode="lines+markers",
                name=RadonCc.entity_type_display(entity_type),
            ),
        )

    style_figure(fig, layout={"yaxis_title": "Cyclomatic Complexity"})

    return fig.to_html()
