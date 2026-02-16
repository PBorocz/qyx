"""Render all Radon:HAL Metrics for page templating."""

from argparse import Namespace
from datetime import datetime

import plotly.graph_objects as go

from qyx.constants import ReportLevel
from qyx.tools.base import Project, Scan
from qyx.tools.radon.models import RadonHal, query_hal
from qyx.web.plotly import SERIES_COLORS, custom_labels, style_figure


def hal_0(args: Namespace, project: Project, scan: Scan = None) -> list:
    row = query_hal(args, ReportLevel.SUMMARY, scan=scan)
    return_ = []
    for attr in RadonHal.attrs():
        value = Namespace(
            metric=attr.display + " " + attr.calculation,
            value=getattr(row, attr.name),
        )
        return_.append(value)
    return return_


def hal_1(args: Namespace, project: Project, scan: Scan = None) -> dict:
    rows, _ = query_hal(args, ReportLevel.DIRECTORY, scan)
    thead = [attr.display for attr in RadonHal.attrs()]
    tbody = []
    for row in rows:
        tbody_row = Namespace(directory=row.directory, values=[])
        for attr in RadonHal.attrs():
            # Since these are aggregated to the directory level, all the attributes are Float!
            tbody_row.values.append(getattr(row, attr.name))
        tbody.append(tbody_row)

    return dict(thead=thead, tbody=tbody)


def hal_2(args: Namespace, project: Project, scan: Scan = None) -> dict:
    rows, _ = query_hal(args, ReportLevel.FILE, scan)
    thead = [attr.display for attr in RadonHal.attrs()]
    tbody = []
    for row in rows:
        tbody_row = Namespace(directory_filename=f"{row.directory}/{row.filename}", values=[])
        for attr in RadonHal.attrs():
            if attr.type == "float":  # HARDCODE
                s_value = f"{getattr(row, attr.name):.2f}"
            elif attr.type == "int":  # HARDCODE
                s_value = f"{getattr(row, attr.name):,d}"
            tbody_row.values.append(s_value)
        tbody.append(tbody_row)
    return dict(thead=thead, tbody=tbody)


def hal_3(args: Namespace, project: Project, scan: Scan = None) -> dict:
    rows, _ = query_hal(args, ReportLevel.DETAIL, scan)
    thead = [attr.display for attr in RadonHal.attrs()]
    tbody = []
    for row in rows:
        tbody_row = Namespace(
            directory_filename=f"{row.directory}/{row.filename}",
            name=row.name,
            values=[],
        )
        for attr in RadonHal.attrs():
            if attr.type == "float":  # HARDCODE
                s_value = f"{getattr(row, attr.name):.2f}"
            elif attr.type == "int":  # HARDCODE
                s_value = f"{getattr(row, attr.name):,d}"
            tbody_row.values.append(s_value)
        tbody.append(tbody_row)
    return dict(thead=thead, tbody=tbody)


def hal_d(args: Namespace, project: Project, scan: Scan) -> list[Namespace]:
    metric_row = query_hal(args, ReportLevel.DERIVED, project=project, scan=scan)
    rows = []
    for name, attr in [
        ("Mean Bugs per kLOC", "bugs_d"),
        ("Mean Difficulty", "difficulty_d"),
        ("Mean Effort per LOC", "effort_d"),
        ("Composite Score", "composite_d"),
    ]:
        rows.append(
            Namespace(
                name=name,
                score=getattr(metric_row, attr).score,
                grade=getattr(metric_row, attr).grade,
                color=getattr(metric_row, attr).color,
            ),
        )
    return rows


def hal_h(args: Namespace, project: Project, scan: Scan = None) -> dict[str, str]:
    _, messages, transposed, _ = query_hal(args, ReportLevel.HISTORY, project=project, last=None)
    if not transposed:
        return dict()

    # This is a bit unique in that we create a chart for EACH separate metric!
    radon_names = {attr.name: attr.display for attr in RadonHal.attrs()}
    charts = dict()
    for metric, values_by_timestamp in transposed.items():
        fig = go.Figure()
        x_values = [datetime.fromisoformat(ts_) for ts_ in values_by_timestamp.keys()]
        y_values = [round(value, 2) for value in values_by_timestamp.values()]
        labels = custom_labels(radon_names[metric], messages, x_values, y_values)
        fig.add_trace(
            go.Scatter(
                x=x_values,
                y=y_values,
                customdata=labels,
                hovertemplate="%{customdata}",
                line_color=SERIES_COLORS[0],
                marker_color=SERIES_COLORS[0],
                mode="lines+markers",
                name=radon_names[metric],
            ),
        )
        style_figure(
            fig,
            layout={
                "yaxis_title": radon_names[metric],
            },
        )
        charts[metric] = fig.to_html()
    return charts
