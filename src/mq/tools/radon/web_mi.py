"""MI - Level 0."""

from argparse import Namespace
from datetime import datetime

from fasthtml import common as fh
import plotly.graph_objects as go

from mq.constants import ReportLevel
from mq.tools.base import Project, Scan
from mq.tools.radon.models import query_mi
from mq.web import SERIES_COLORS
from mq.utils.plotly_styles import style_figure


def mi_0(args: Namespace, scan: Scan, project: Project = None):
    row = query_mi(args, ReportLevel.SUMMARY, scan=scan)

    # fmt: off
    t_head = (
        fh.Th("Composite Maintainability",  style="text-align: left", colspan=ReportLevel.FILE),
    )
    t_body = (
        fh.Th("Score"             , style="text-align: left" ),
        fh.Th(f"{row.mi_mean:.2f}", style="text-align: right"),
    )
    # fmt: on

    return (
        fh.Table(fh.Thead(*t_head), fh.Tbody(*t_body), id="mi_0"),
        fh.Script("new Tablesort(document.getElementById('mi_0'));"),
    )


def mi_1(args: Namespace, scan: Scan, project: Project = None):
    rows, _, _, _ = query_mi(args, ReportLevel.DIRECTORY, scan)

    # fmt: off
    t_head = fh.Tr(
        fh.Th("Directory"            , scope="col", style="text-align: left"),
        fh.Th("Maintainability Index", scope="col", style="text-align: right"),
    )

    t_body = []
    for row in rows:
        t_row = fh.Tr(
            fh.Td(row.directory       , style="text-align: left"),
            fh.Td(f"{row.mi_mean:.2f}", style="text-align: right"),
        )
        t_body.append(t_row)
    # fmt: on

    return (
        fh.Table(
            fh.Thead(*t_head),
            fh.Tbody(*t_body),
            id="mi_1",
        ),
        fh.Script("new Tablesort(document.getElementById('mi_1'));"),
    )


def mi_2(args: Namespace, scan: Scan, project: Project = None):
    rows, _, _ = query_mi(args, ReportLevel.FILE, scan)

    # fmt: off
    t_head = fh.Tr(
        fh.Th("Directory"            , scope="col", style="text-align: left"),
        fh.Th("Filename"             , scope="col", style="text-align: left"),
        fh.Th("Maintainability Index", scope="col", style="text-align: right"),
        fh.Th("Rank"                 , scope="col", style="text-align: center"),
    )

    t_body = []
    for row in rows:
        t_row = fh.Tr(
            fh.Td(row.directory   , style="text-align: left"),
            fh.Td(row.filename    , style="text-align: left"),
            fh.Td(f"{row.mi:.2f}" , style="text-align: right"),
            fh.Td(row.rank        , style="text-align: center"),
        )
        t_body.append(t_row)
    # fmt: on

    return (
        fh.Table(
            fh.Thead(*t_head),
            fh.Tbody(*t_body),
            id="mi_2",
        ),
        fh.Script("new Tablesort(document.getElementById('mi_2'));"),
    )


def mi_d(args: Namespace, project: Project, scan: Scan):
    row = query_mi(args, ReportLevel.DERIVED, project=project, scan=scan)
    return (
        fh.Table(
            fh.Thead(
                fh.Tr(
                    fh.Th("Metric", scope="col", style="text-align: left"),
                    fh.Th("Value", scope="col", style="text-align: center"),
                    fh.Th("Grade", scope="col", style="text-align: center"),
                ),
            ),
            fh.Tbody(
                fh.Tr(
                    fh.Td("Maintainability", style="text-align: left"),
                    fh.Td(f"{row.mi_d.score:.0f}%", style="text-align: center;"),
                    fh.Td(
                        f"{row.mi_d.grade}",
                        style=f"text-align: center; color: var(--pico-muted-color); background-color: {row.mi_d.color}",
                    ),
                ),
            ),
        ),
    )


def mi_h(args: Namespace, project: Project, scan: Scan = None):
    """Render the maintainability index chart."""
    _, transposed, _ = query_mi(args, ReportLevel.HISTORY, project=project, last=None)
    dt_complexity = transposed["mi"]
    x_values = [datetime.fromisoformat(ts_) for ts_ in dt_complexity.keys()]
    y_values = list(dt_complexity.values())

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=y_values,
            mode="lines+markers",
            marker_color=SERIES_COLORS[0],
            line_color=SERIES_COLORS[0],
            hovertemplate="%{y:.2f}<br>As Of: %{x|%Y-%m-%d %H:%M}<br><extra></extra>",
        ),
    )
    style_figure(
        fig,
        layout={
            "yaxis_title": "Maintainability Index",
        },
    )
    return fig.to_html().encode()
