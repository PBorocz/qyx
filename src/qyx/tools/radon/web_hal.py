"""HAL - Level 0."""

from argparse import Namespace
from datetime import datetime

import plotly.graph_objects as go
from fasthtml import common as fh

from qyx.constants import ReportLevel
from qyx.tools.base import Project, Scan
from qyx.tools.radon.models import RadonHal, query_hal
from qyx.web.plotly import SERIES_COLORS, custom_labels, style_figure


def hal_0(args: Namespace, scan: Scan, project: Project = None):
    row = query_hal(args, ReportLevel.SUMMARY, scan=scan)

    # fmt: off
    t_head = fh.Tr(
        fh.Th("Metric", scope="col", style="text-align: left" ),
        fh.Th("Value" , scope="col", style="text-align: right"),
    )

    t_body = []
    for attr in RadonHal.attrs():
        t_row = fh.Tr(
            fh.Th(fh.Span(attr.display), " ", fh.Small(attr.calculation), style="text-align: left" ),
            fh.Td(f"{getattr(row, attr.name):.1f}"                      , style="text-align: right"),
        )
        t_body.append(t_row)
    # fmt: on

    return (
        fh.Table(
            fh.Thead(*t_head),
            fh.Tbody(*t_body),
            id="hal_0",
        ),
        fh.Script("new Tablesort(document.getElementById('hal_0'));"),
    )


def hal_1(args: Namespace, scan: Scan, project: Project = None):
    rows, mean_means = query_hal(args, ReportLevel.DIRECTORY, scan)

    t_tr = [fh.Th("Metric", scope="col", style="text-align: left")]
    for attr in RadonHal.attrs():
        t_tr.append(fh.Th(attr.display, scope="col", style="text-align: right"))
    t_head = fh.Tr(*t_tr)

    t_body = []
    for row in rows:
        t_row = [fh.Th(row.directory, style="text-align: left")]
        for attr in RadonHal.attrs():
            t_row.append(fh.Td(f"{getattr(row, attr.name):.2f}", style="text-align: right"))
        t_body.append(fh.Tr(*t_row))

    return (
        fh.Table(
            fh.Thead(*t_head),
            fh.Tbody(*t_body),
            id="hal_1",
        ),
        fh.Script("new Tablesort(document.getElementById('hal_1'));"),
    )


def hal_2(args: Namespace, scan: Scan, project: Project = None):
    rows, _ = query_hal(args, ReportLevel.FILE, scan)

    t_tr = [fh.Th("File", scope="col", style="text-align: left")]
    for attr in RadonHal.attrs():
        t_tr.append(fh.Th(attr.display, scope="col", style="text-align: right"))
    t_head = fh.Tr(*t_tr)

    t_body = []
    for row in rows:
        t_row = [fh.Th(f"{row.directory}/{row.filename}", style="text-align: left")]
        for attr in RadonHal.attrs():
            if attr.type == "float":
                s_value = f"{getattr(row, attr.name):.2f}"
            elif attr.type == "int":
                s_value = f"{getattr(row, attr.name):,d}"
            t_row.append(fh.Td(s_value, style="text-align: right"))
        t_body.append(fh.Tr(*t_row))

    return (
        fh.Table(
            fh.Thead(*t_head),
            fh.Tbody(*t_body),
            id="hal_2",
        ),
        fh.Script("new Tablesort(document.getElementById('hal_2'));"),
    )


def hal_3(args: Namespace, scan: Scan, project: Project = None):
    rows, _ = query_hal(args, ReportLevel.DETAIL, scan)

    t_tr = [
        fh.Th("File", scope="col", style="text-align: left"),
        fh.Th("Name", scope="col", style="text-align: left"),
    ]
    for attr in RadonHal.attrs():
        t_tr.append(fh.Th(attr.display, scope="col", style="text-align: right"))
    t_head = fh.Tr(*t_tr)

    t_body = []
    for row in rows:
        t_row = [
            fh.Td(f"{row.directory}/{row.filename}", style="text-align: left"),
            fh.Td(row.name, style="text-align: left"),
        ]
        for attr in RadonHal.attrs():
            if attr.type == "float":
                s_value = f"{getattr(row, attr.name):.3f}"
            elif attr.type == "int":
                s_value = f"{getattr(row, attr.name):,d}"
            t_row.append(fh.Td(s_value, style="text-align: right"))
        t_body.append(fh.Tr(*t_row))

    return (
        fh.Table(
            fh.Thead(*t_head),
            fh.Tbody(*t_body),
            id="hal_3",
        ),
        fh.Script("new Tablesort(document.getElementById('hal_3'));"),
    )


def hal_d(args: Namespace, project: Project, scan: Scan):
    row = query_hal(args, ReportLevel.DERIVED, project=project, scan=scan)

    t_head = fh.Tr(
        fh.Th("Metric", scope="col", style="text-align: left"),
        fh.Th("Value", scope="col", style="text-align: right"),
        fh.Th("Grade", scope="col", style="text-align: center"),
    )

    t_body = (
        fh.Tr(
            fh.Td("Mean Bugs per kLOC", style="text-align: left"),
            fh.Td(f"{row.bugs_d.score:.1f}", style="text-align: right"),
            fh.Td(
                f"{row.bugs_d.grade}",
                style=f"text-align: center; color: var(--pico-muted-color); background-color: {row.bugs_d.color}",
            ),
        ),
        fh.Tr(
            fh.Td("Mean Difficulty", style="text-align: left"),
            fh.Td(f"{row.difficulty_d.score:.1f}", style="text-align: right"),
            fh.Td(
                f"{row.difficulty_d.grade}",
                style=f"text-align: center; color: var(--pico-muted-color); background-color: {row.difficulty_d.color}",
            ),
        ),
        fh.Tr(
            fh.Td("Mean Effort per LOC", style="text-align: left"),
            fh.Td(f"{row.effort_d.score:.1f}", style="text-align: right"),
            fh.Td(
                f"{row.effort_d.grade}",
                style=f"text-align: center; color: var(--pico-muted-color); background-color: {row.effort_d.color}",
            ),
        ),
        fh.Tr(
            fh.Td("Composite Score", style="text-align: left"),
            fh.Td(f"{row.composite_d.score:.1f}", style="text-align: right"),
            fh.Td(
                f"{row.composite_d.grade}",
                style=f"text-align: center; color: var(--pico-muted-color); background-color: {row.composite_d.color}",
            ),
        ),
    )

    return (
        fh.Table(
            fh.Thead(t_head),
            fh.Tbody(*t_body),
        ),
    )


def hal_h(args: Namespace, project: Project, scan: Scan = None) -> dict:
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

        charts[metric] = fig.to_html().encode()

    return charts
