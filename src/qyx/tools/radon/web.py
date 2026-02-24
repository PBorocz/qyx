"""Report data obo running 'radon' tool."""

import logging
from argparse import Namespace
from datetime import datetime

from bottle import request

from qyx.constants import ViewContext as Vc
from qyx.tools.base import Project, Scan, State
from qyx.tools.radon import models as rm
from qyx.tools.radon.models import RadonCc
from qyx.tools.radon.models import RadonHal
from qyx.web import get_analysis_selector, get_project_selector
from qyx.web.page import render_page, render_partial

import plotly.graph_objects as go

from qyx.web.plotly import SERIES_COLORS, custom_labels, style_figure


log = logging.getLogger(__name__)


################################################################################################
# Page layout...
################################################################################################
def render(template: str = "radon::page.html") -> str:
    """Render the tool's primary page."""
    return render_page(
        "QYX-RADON",
        template,
        project_options=get_project_selector(),
        analysis_options=get_analysis_selector(),
        set_project="/partials/set_project/radon",
        set_analysis="/partials/set_project/radon",
    )


def render_content() -> str:
    """Render the content portion (ie. body) of the page."""
    args = request.app.args

    # Get the arguments passed from the HTMX get context:
    s_project_id = request.query.project
    analysis = request.query.analysis.lower()

    # Find the project...
    project = Project.get(Project.id == int(s_project_id))
    if not s_project_id or not project:
        return render_partial("base::fragments/_no_project_yet.html")

    # Find the most recent scan on behalf of this project...
    scan = Scan.get_most_recent(project, "radon", analysis)
    if not scan:
        return render_partial("base::fragments/_no_scans_yet.html")

    # Populate the return context with all the data and charts
    # necessary to render the page's body:
    context = Namespace()
    # NOTE: Some of these might return None if the level is not
    # applicable or defined for the respective analysis, and that's OK!
    setattr(context, f"{analysis}_as_of", scan.as_of_display(collapse_today=True))
    setattr(context, f"{analysis}_0", _view_data_by_level(args, "0", project, scan, analysis))
    setattr(context, f"{analysis}_1", _view_data_by_level(args, "1", project, scan, analysis))
    setattr(context, f"{analysis}_2", _view_data_by_level(args, "2", project, scan, analysis))
    setattr(context, f"{analysis}_3", _view_data_by_level(args, "3", project, scan, analysis))
    setattr(context, f"{analysis}_d", _view_data_by_level(args, "d", project, scan, analysis))
    setattr(context, f"{analysis}_h", _view_data_by_level(args, "h", project, scan, analysis))

    # Remember what we just processed for next time through (used by
    # the get_project/analysis_selector's above)
    State.update(args, project=project.name, analysis=analysis)

    # Template to return is based on the particular analysis requested:
    template: str = f"radon::{analysis}/{analysis}.htmx"

    return render_partial(template, **context.__dict__)


def _view_data_by_level(args: Namespace, level: str, project: Project, scan: Scan, analysis: str) -> dict | None:
    """Dispatch to the appropriate view method to get data obo the specified level fand analysis."""
    # First, lookup the method below based on the analysis and level requested.
    view_method_name = f"{analysis}_{level}"
    view_method = globals().get(view_method_name)
    if not view_method:
        log.warning(f"no method found, skipping {view_method_name=}")
        return None
    return view_method(args, project, scan)


################################################################################
# CC
################################################################################
def cc_0(args: Namespace, project: Project, scan: Scan, context: Vc = Vc.TOOL_HOME) -> dict:
    return dict(rows=rm.query_cc_0(args, scan))


def cc_1(args: Namespace, project: Project, scan: Scan) -> dict:
    return dict(rows=rm.query_cc_1(args, scan))


def cc_2(args: Namespace, project: Project, scan: Scan) -> dict:
    return dict(rows=rm.query_cc_2(args, scan))


def cc_3(args: Namespace, project: Project, scan: Scan) -> dict:
    return dict(rows=rm.query_cc_3(args, scan))


def cc_d(args: Namespace, project: Project, scan: Scan) -> dict:
    return None


def cc_h(args: Namespace, project: Project, scan: Scan) -> str:
    """Render our chart to display Radon CC information."""
    _, messages, transposed, _ = rm.query_cc_h(project)

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


################################################################################
# HAL
################################################################################
def hal_0(args: Namespace, project: Project, scan: Scan, context: Vc = Vc.TOOL_HOME) -> list:
    row = rm.query_hal_0(args, project, scan)
    rows = []
    for metric, attr in [
        ("Composite Score", "composite_d"),
        ("Mean Bugs per kLOC", "bugs_d"),
        ("Mean Difficulty", "difficulty_d"),
        ("Mean Effort per LOC", "effort_d"),
    ]:
        rows.append(
            Namespace(
                metric=metric,
                score=getattr(row, attr).score,
                grade=getattr(row, attr).grade,
                color=getattr(row, attr).color,
            ),
        )
    if context == Vc.TOOL_HOME:
        # Only put the detailed values out for the tool home page, not the Dashboard.
        for attr in RadonHal.attrs():
            value = Namespace(
                metric=attr.display + " " + attr.calculation,
                score=getattr(row, attr.name),
                grade="",
                color="",
            )
            rows.append(value)
    return rows


def hal_1(args: Namespace, project: Project, scan: Scan = None) -> dict:
    rows, _ = rm.query_hal_1(scan)
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
    rows, _ = rm.query_hal_2(scan)
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
    rows, _ = rm.query_hal_3(scan)
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


def hal_h(args: Namespace, project: Project, scan: Scan = None) -> dict[str, str]:
    _, messages, transposed, _ = rm.query_hal_h(project)
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


################################################################################
# MI
################################################################################
def mi_0(args: Namespace, project: Project, scan: Scan, context: Vc = Vc.TOOL_HOME) -> dict[str, float | None]:
    return dict(metric=rm.query_mi_0(args, scan))


def mi_1(args: Namespace, project: Project, scan: Scan):
    _, rows = rm.query_mi_1(args, scan)
    return dict(rows=rows)


def mi_2(args: Namespace, project: Project, scan: Scan):
    _, rows = rm.query_mi_2(args, scan)
    return dict(rows=rows)


def mi_d(args: Namespace, project: Project, scan: Scan):
    """Stub to make this analysis match others."""
    return None


def mi_h(args: Namespace, project: Project, scan: Scan):
    """Render the maintainability index chart."""
    messages, rows, roc = rm.query_mi_h(project)
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


################################################################################
# RAW
################################################################################
def raw_0(args: Namespace, project: Project, scan: Scan, context: Vc = Vc.TOOL_HOME):
    return dict(row=rm.query_raw_0(scan))


def raw_1(args: Namespace, project: Project, scan: Scan):
    return dict(rows=rm.query_raw_1(scan)[0])


def raw_2(args: Namespace, project: Project, scan: Scan):
    return dict(rows=rm.query_raw_2(scan))


def raw_d(args: Namespace, project: Project, scan: Scan):
    """Stub to make this analysis match others."""
    return None


def raw_h(args: Namespace, project: Project, scan: Scan = None):
    """Create chart obo all Raw metrics."""
    _, messages, transposed, _, _ = rm.query_raw_h(project)

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
