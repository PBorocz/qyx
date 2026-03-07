"""Report data obo running 'radon' tool."""

import logging
from argparse import Namespace
from datetime import datetime
from types import SimpleNamespace as Sns

from bottle import request

from qyx.constants import ViewContext as Vc
from qyx.tools.base import Scan
from qyx.tools.radon import models as rm
from qyx.tools.radon.models import RadonCc
from qyx.tools.radon.models import RadonHal
from qyx.web.page import render, render_analyses, render_content

import plotly.graph_objects as go

from qyx.web.plotly import SERIES_COLORS, custom_labels, style_figure


log = logging.getLogger(__name__)


################################################################################################
# Routing/View methods
################################################################################################
def view(template: str = "radon::page.html") -> str:
    """View callback to render the entire tool page: project selector, analysis selector and body content."""
    o_tool = request.app.args.tools["radon"]
    return render(o_tool, template, get_content)


def view_analyses() -> str:
    """View callback when project changes to render BOTH update analysis selector *AND* update body on an OOB basis."""
    o_tool = request.app.args.tools["radon"]
    project: str = request.query.project
    return render_analyses(o_tool, project, get_content)


def view_content() -> str:
    """View callback for when a new analysis is selected, just need to update the body content directly."""
    o_tool = request.app.args.tools["radon"]
    project: str = request.query.project
    analysis: str = request.query.analysis.lower()
    return render_content(project, o_tool, analysis, get_content)


################################################################################################
def get_content(scan: Scan) -> Sns:
    """Populate our tool's home page data based on the specified scan."""
    args = request.app.args

    if scan.git_commit_message:
        display = f"{scan.as_of_display(collapse_today=True)} - {scan.git_commit_message}"
    else:
        display = f"{scan.as_of_display(collapse_today=True)}"

    context = Sns(tool=scan.tool, analysis=scan.analysis)
    setattr(context, f"{scan.analysis}_as_of", display)
    setattr(context, f"{scan.analysis}_0", _get_content_by_level(args, "0", scan))
    setattr(context, f"{scan.analysis}_1", _get_content_by_level(args, "1", scan))
    setattr(context, f"{scan.analysis}_2", _get_content_by_level(args, "2", scan))
    setattr(context, f"{scan.analysis}_3", _get_content_by_level(args, "3", scan))
    setattr(context, f"{scan.analysis}_h", _get_content_by_level(args, "h", scan))
    return context


def _get_content_by_level(args: Namespace, level: str, scan: Scan) -> dict | Sns | None:
    """Dispatch to the appropriate view method to get data obo the specified level fand analysis."""
    # First, lookup the method below based on the analysis and level requested.
    view_method_name = f"view_{scan.analysis}_{level}"
    view_method = globals().get(view_method_name)
    if view_method:
        return view_method(args, scan)
    return None


################################################################################
# CC
################################################################################
def view_cc_0(args: Namespace, scan: Scan, context: Vc = Vc.TOOL_HOME) -> dict:
    return rm.query_cc_0(args, scan)


def view_cc_1(args: Namespace, scan: Scan) -> dict:
    return rm.query_cc_1(args, scan)


def view_cc_2(args: Namespace, scan: Scan) -> dict:
    return rm.query_cc_2(args, scan)


def view_cc_3(args: Namespace, scan: Scan) -> dict:
    return rm.query_cc_3(args, scan)


def view_cc_h(args: Namespace, scan: Scan) -> str:
    """Render our chart to display Radon CC information."""
    result = rm.query_cc_h(scan.request.project)

    fig = go.Figure()
    for i, entity_type in enumerate(("C", "F", "M")):  # HARD-CODE!
        values_by_timestamp = result.transposed[entity_type]
        x_values = [datetime.fromisoformat(ts_) for ts_ in values_by_timestamp.keys()]
        y_values = [round(value, 2) for value in values_by_timestamp.values()]
        labels = custom_labels(f"({entity_type})", result.messages, x_values, y_values)
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


################################################################################
# HAL
################################################################################
def view_hal_0(args: Namespace, scan: Scan, context: Vc = Vc.TOOL_HOME) -> list:
    result = rm.query_hal_0(args, scan)
    rows = []
    for metric, attr in [
        ("Composite Score", "composite_d"),
        ("Mean Bugs per kLOC", "bugs_d"),
        ("Mean Difficulty", "difficulty_d"),
        ("Mean Effort per LOC", "effort_d"),
    ]:
        rows.append(
            Sns(
                metric=metric,
                score=getattr(result, attr).score,
                grade=getattr(result, attr).grade,
                color=getattr(result, attr).color,
            ),
        )
    if context == Vc.TOOL_HOME:
        # Only put the detailed values out for the tool home page, not the Dashboard.
        for attr in RadonHal.attrs():
            value = Sns(
                metric=attr.display + " " + attr.calculation,
                score=getattr(result, attr.name),
                grade="",
                color="",
            )
            rows.append(value)
    return rows


def view_hal_1(args: Namespace, scan: Scan = None) -> dict:
    result = rm.query_hal_1(scan)
    thead = [attr.display for attr in RadonHal.attrs()]
    tbody = []
    for row in result.rows:
        tbody_row = Sns(directory=row.directory, values=[])
        for attr in RadonHal.attrs():
            # Since these are aggregated to the directory level, all the attributes are Float!
            tbody_row.values.append(getattr(row, attr.name))
        tbody.append(tbody_row)

    return dict(thead=thead, tbody=tbody)


def view_hal_2(args: Namespace, scan: Scan = None) -> dict:
    result = rm.query_hal_2(scan)
    thead = [attr.display for attr in RadonHal.attrs()]
    tbody = []
    for row in result.rows:
        tbody_row = Sns(directory_filename=f"{row.directory}/{row.filename}", values=[])
        for attr in RadonHal.attrs():
            if attr.type == "float":  # HARDCODE
                s_value = f"{getattr(row, attr.name):.2f}"
            elif attr.type == "int":  # HARDCODE
                s_value = f"{getattr(row, attr.name):,d}"
            tbody_row.values.append(s_value)
        tbody.append(tbody_row)
    return dict(thead=thead, tbody=tbody)


def view_hal_3(args: Namespace, scan: Scan = None) -> dict:
    result = rm.query_hal_3(scan)
    thead = [attr.display for attr in RadonHal.attrs()]
    tbody = []
    for row in result.rows:
        tbody_row = Sns(
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


def view_hal_h(args: Namespace, scan: Scan = None) -> dict[str, str]:
    result = rm.query_hal_h(scan.request.project)
    if not result.transposed:
        return dict()

    # This is a bit unique in that we create a chart for EACH separate metric!
    radon_names = {attr.name: attr.display for attr in RadonHal.attrs()}
    charts = dict()
    for metric, values_by_timestamp in result.transposed.items():
        fig = go.Figure()
        x_values = [datetime.fromisoformat(ts_) for ts_ in values_by_timestamp.keys()]
        y_values = [round(value, 2) for value in values_by_timestamp.values()]
        labels = custom_labels(radon_names[metric], result.messages, x_values, y_values)
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


################################################################################
# MI
################################################################################
def view_mi_0(args: Namespace, scan: Scan, context: Vc = Vc.TOOL_HOME) -> dict[str, float | None]:
    return rm.query_mi_0(args, scan)


def view_mi_1(args: Namespace, scan: Scan):
    return rm.query_mi_1(args, scan)


def view_mi_2(args: Namespace, scan: Scan):
    return rm.query_mi_2(args, scan)


def view_mi_h(args: Namespace, scan: Scan):
    """Render the maintainability index chart."""
    result = rm.query_mi_h(scan.request.project)
    x_values = [datetime.fromisoformat(ts_) for ts_ in result.rows.keys()]
    y_values = [round(value, 2) for value in result.rows.values()]
    labels = custom_labels("", result.messages, x_values, y_values)
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


################################################################################
# RAW
################################################################################
def view_raw_0(args: Namespace, scan: Scan, context: Vc = Vc.TOOL_HOME):
    return rm.query_raw_0(args, scan)


def view_raw_1(args: Namespace, scan: Scan):
    return rm.query_raw_1(scan)


def view_raw_2(args: Namespace, scan: Scan):
    return rm.query_raw_2(scan)


def view_raw_h(args: Namespace, scan: Scan = None):
    """Create chart obo all Raw metrics."""
    result = rm.query_raw_h(scan.request.project)

    fig = go.Figure()
    for i, (metric, dt_rows) in enumerate(list(result.transposed.items())):
        x_values = [datetime.fromisoformat(ts_) for ts_ in dt_rows.keys()]
        y_values = list(dt_rows.values())
        labels = custom_labels(metric.upper(), result.messages, x_values, y_values)
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
