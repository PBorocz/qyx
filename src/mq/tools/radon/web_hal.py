"""HAL - Level 0."""

from argparse import Namespace
from datetime import datetime

from fasthtml import common as fh
from pygal import DateTimeLine
from pygal.style import Style

from mq.constants import ReportLevel
from mq.tools.base import Project, Scan
from mq.tools.radon.models import RadonHal, query_hal
from mq.web import DEFAULT_CHART_STYLE


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


def hal_h(args: Namespace, project: Project, scan: Scan = None):
    timestamps, transposed, _ = query_hal(args, ReportLevel.HISTORY, project=project, last=None)

    style = Style(**DEFAULT_CHART_STYLE)

    # Create a chart for EACH separate metric!
    charts = dict()
    radon_names = {attr.name: attr.display for attr in RadonHal.attrs()}
    for metric, values_by_timestamp in transposed.items():
        dt_values = [(datetime.fromisoformat(ts_), value) for ts_, value in values_by_timestamp.items()]
        chart = DateTimeLine(
            y_title=radon_names[metric],
            dots_size=1,
            height=500,
            show_legend=False,
            style=style,
            tooltip_border_radius=10,
            x_label_rotation=45,  # Angle labels to prevent overlap
            x_labels_major_every=2,  # Show every 5th label
            x_value_formatter=lambda dt: dt.strftime("%Y-%m-%d %H:%M"),
        )
        chart.add(metric, dt_values)
        charts[metric] = chart.render()

    return charts
