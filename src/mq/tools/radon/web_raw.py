"""Raw - Level 0."""

from argparse import Namespace
from datetime import datetime

from fasthtml import common as fh
import plotly.graph_objects as go

from mq.constants import ReportLevel
from mq.tools.base import Project, Scan
from mq.tools.radon.models import query_raw
from mq.web import SERIES_COLORS
from mq.utils.plotly_styles import style_figure


def raw_0(args: Namespace, scan: Scan, project: Project = None):
    row = query_raw(args, ReportLevel.SUMMARY, scan=scan)

    t_head = fh.Tr(
        fh.Th(
            "SLOC",
            scope="col",
            style="text-align: center",
        ),
        fh.Th(
            "Multi",
            scope="col",
            style="text-align: center",
        ),
        fh.Th(
            "Comment",
            scope="col",
            style="text-align: center",
        ),
        fh.Th(
            "Blank",
            scope="col",
            style="text-align: center",
        ),
        fh.Th(
            fh.B("Total"),
            scope="col",
            style="text-align: center",
        ),
    )

    t_body = fh.Tr(
        fh.Td(
            f"{row.sloc:,}",
            " ",
            fh.Small(f"({row.sloc_p:.1f}%)"),
            style="text-align: center",
        ),
        fh.Td(
            f"{row.multi:,}",
            " ",
            fh.Small(f"({row.multi_p:.1f}%)"),
            style="text-align: center",
        ),
        fh.Td(
            f"{row.comments:,}",
            " ",
            fh.Small(f"({row.comments_p:.1f}%)"),
            style="text-align: center",
        ),
        fh.Td(
            f"{row.blank:,}",
            " ",
            fh.Small(f"({row.blank_p:.1f}%)"),
            style="text-align: center",
        ),
        fh.Td(
            fh.B(f"{row.loc:,}"),
            style="text-align: center",
        ),
    )

    return (
        fh.Table(
            fh.Thead(t_head),
            fh.Tbody(t_body),
            id="raw_0",
        ),
        fh.Script("new Tablesort(document.getElementById('raw_0'));"),
    )


def raw_1(args: Namespace, scan: Scan, project: Project = None):
    rows, totals = query_raw(args, ReportLevel.DIRECTORY, scan)

    # fmt: off
    t_head = fh.Tr(
        fh.Th("Directory" , scope="col", style="text-align: left"),
        fh.Th("SLOC"      , scope="col", style="text-align: right"),
        fh.Th("Comment"   , scope="col", style="text-align: right"),
        fh.Th("Multi"     , scope="col", style="text-align: right"),
        fh.Th("Blank"     , scope="col", style="text-align: right"),
        fh.Th("Total"     , scope="col", style="text-align: right"),
    )
    # fmt: on

    t_body = []
    for row in rows:
        # fmt: off
        t_row = fh.Tr(
            fh.Td(row.directory       , style="text-align: left"),
            fh.Td(f"{row.sloc:,}"     , style="text-align: right"),
            fh.Td(f"{row.comments:,}" , style="text-align: right"),
            fh.Td(f"{row.multi:,}"    , style="text-align: right"),
            fh.Td(f"{row.blank:,}"    , style="text-align: right"),
            fh.Td(f"{row.loc:,}"      , style="text-align: right"),
        )
        # fmt: on
        t_body.append(t_row)

    return (
        fh.Table(
            fh.Thead(t_head),
            fh.Tbody(*t_body),
            fh.Tfoot(),
            id="raw_1",
        ),
        fh.Script("new Tablesort(document.getElementById('raw_1'));"),
    )


def raw_2(args: Namespace, scan: Scan, project: Project = None):
    rows = query_raw(args, ReportLevel.FILE, scan)

    # fmt: off
    t_head = fh.Tr(
        fh.Th("Directory" , scope="col", style="text-align: left"),
        fh.Th("File"      , scope="col", style="text-align: left"),
        fh.Th("SLOC"      , scope="col", style="text-align: right"),
        fh.Th("Comment"   , scope="col", style="text-align: right"),
        fh.Th("Multi"     , scope="col", style="text-align: right"),
        fh.Th("Blank"     , scope="col", style="text-align: right"),
        fh.Th("Total"     , scope="col", style="text-align: right"),
    )
    # fmt: on

    t_body = []
    for row in rows:
        # fmt: off
        t_row = fh.Tr(
            fh.Td(row.directory       , style="text-align: left"),
            fh.Td(row.filename        , style="text-align: left"),
            fh.Td(f"{row.sloc:,}"     , style="text-align: right"),
            fh.Td(f"{row.comments:,}" , style="text-align: right"),
            fh.Td(f"{row.multi:,}"    , style="text-align: right"),
            fh.Td(f"{row.blank:,}"    , style="text-align: right"),
            fh.Td(f"{row.loc:,}"      , style="text-align: right"),
        )
        # fmt: on
        t_body.append(t_row)

    return (
        fh.Table(
            fh.Thead(t_head),
            fh.Tbody(*t_body),
            fh.Tfoot(),
            id="raw_2",
        ),
        fh.Script("new Tablesort(document.getElementById('raw_2'));"),
    )


def raw_h(args: Namespace, project: Project, scan: Scan = None):
    """Create chart obo all Raw metrics."""
    _, transposed, _, _ = query_raw(args, ReportLevel.HISTORY, project=project, last=None)

    fig = go.Figure()
    for i, (metric, dt_rows) in enumerate(list(transposed.items())):
        x_values = [datetime.fromisoformat(ts_) for ts_ in dt_rows.keys()]
        y_values = list(dt_rows.values())
        fig.add_trace(
            go.Scatter(
                line_color=SERIES_COLORS[i % len(SERIES_COLORS)],
                marker_color=SERIES_COLORS[i % len(SERIES_COLORS)],
                mode="lines+markers",
                name=metric.upper(),
                x=x_values,
                y=y_values,
                hovertemplate="<b>%{y}</b> "
                + f"{metric.upper()}'s"
                + "<br>As Of: %{x|%Y-%m-%d %H:%M}<br>"
                + "<extra></extra>",
            ),
        )

    style_figure(
        fig,
        layout={
            "yaxis_title": "Number of Lines",
        },
    )

    return fig.to_html().encode()
