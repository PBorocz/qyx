"""CC - Level 0."""

from argparse import Namespace
from datetime import datetime

import plotly.graph_objects as go
from fasthtml import common as fh

from mq.constants import ReportLevel
from mq.tools.base import Project, Scan
from mq.tools.radon import RadonCcEntityType
from mq.tools.radon.models import query_cc
from mq.web.plotly import SERIES_COLORS, custom_labels, style_figure


def cc_0(args: Namespace, scan: Scan, project: Project = None):
    rows = query_cc(args, ReportLevel.SUMMARY, scan=scan)

    # fmt: off
    t_head = fh.Tr(
        fh.Th("Entity Type"           , scope="col", style="text-align: left"),
        fh.Th("Cyclomatic Complexity" , scope="col", style="text-align: right"),
    )

    t_body = []
    for row in rows:
        t_row = fh.Tr(
            fh.Td(RadonCcEntityType(row.entity_type).plural, style="text-align: left"),
            fh.Td(f"{row.mean_complexity:.1f}"             , style="text-align: right"),
        )
        t_body.append(t_row)
    # fmt: on

    return (
        fh.Table(
            fh.Thead(t_head),
            fh.Tbody(*t_body),
            fh.Tfoot(),
            id="cc_0",
        ),
        fh.Script("new Tablesort(document.getElementById('cc_0'));"),
    )


def cc_1(args: Namespace, scan: Scan, project: Project = None):
    rows = query_cc(args, ReportLevel.DIRECTORY, scan=scan)

    # fmt: off
    t_head = fh.Tr(
        fh.Th("Directory"   , scope="col", style="text-align: left"),
        fh.Th("Entity Type" , scope="col", style="text-align: left"),
        fh.Th("Complexity"  , scope="col", style="text-align: right"),
        fh.Th("Rank"        , scope="col", style="text-align: center"),
    )
    # fmt: on

    t_body = []
    # fmt: off
    for row in rows:
        t_row = fh.Tr(
            fh.Td(row.directory                             , style="text-align: left"),
            fh.Td(RadonCcEntityType(row.entity_type).plural , style="text-align: left"),
            fh.Td(f"{row.mean_complexity:.2f}"              , style="text-align: right"),
            fh.Td(row.get_rank(row.mean_complexity)         , style="text-align: center"),
        )
        t_body.append(t_row)
    # fmt: off

    return (
        fh.Table(
            fh.Thead(t_head),
            fh.Tbody(*t_body),
            fh.Tfoot(),
            id="cc_1",
        ),
        fh.Script("new Tablesort(document.getElementById('cc_1'));"),
    )


def cc_2(args: Namespace, scan: Scan, project: Project = None):
    rows = query_cc(args, ReportLevel.FILE, scan=scan)

    # fmt: off
    t_head = fh.Tr(
        fh.Th("Directory"   , scope="col", style="text-align: left"),
        fh.Th("Filename"    , scope="col", style="text-align: left"),
        fh.Th("Entity Type" , scope="col", style="text-align: left"),
        fh.Th("Complexity"  , scope="col", style="text-align: right"),
        fh.Th("Rank"        , scope="col", style="text-align: center"),
    )
    # fmt: on

    t_body = []
    # fmt: off
    for row in rows:
        t_row = fh.Tr(
            fh.Td(row.directory                             , style="text-align: left"),
            fh.Td(row.filename                              , style="text-align: left"),
            fh.Td(RadonCcEntityType(row.entity_type).plural , style="text-align: left"),
            fh.Td(f"{row.mean_complexity:.2f}"              , style="text-align: right"),
            fh.Td(row.get_rank(row.mean_complexity)         , style="text-align: center"),
        )
        t_body.append(t_row)
    # fmt: off

    return (
        fh.Table(
            fh.Thead(t_head),
            fh.Tbody(*t_body),
            fh.Tfoot(),
            id="cc_2",
        ),
        fh.Script("new Tablesort(document.getElementById('cc_2'));"),
    )


def cc_3(args: Namespace, scan: Scan, project: Project = None):
    rows = query_cc(args, ReportLevel.DETAIL, scan=scan)

    # fmt: off
    t_head = fh.Tr(
        fh.Th("Directory"   , scope="col", style="text-align: left"),
        fh.Th("Filename"    , scope="col", style="text-align: left"),
        fh.Th("Entity Name" , scope="col", style="text-align: left"),
        fh.Th("Entity Type" , scope="col", style="text-align: left"),
        fh.Th("Complexity"  , scope="col", style="text-align: right"),
        fh.Th("Rank"        , scope="col", style="text-align: center"),
    )
    # fmt: on

    t_body = []
    # fmt: off
    for row in rows:
        t_row = fh.Tr(
            fh.Td(row.directory           , style="text-align: left"),
            fh.Td(row.filename            , style="text-align: left"),
            fh.Td(row.entity_name         , style="text-align: left"),
            fh.Td(row.entity_type         , style="text-align: left"),
            fh.Td(f"{row.complexity:.2f}" , style="text-align: right"),
            fh.Td(row.rank                , style="text-align: center"),
        )
        t_body.append(t_row)
    # fmt: off

    return (
        fh.Table(
            fh.Thead(t_head),
            fh.Tbody(*t_body),
            fh.Tfoot(),
            id="cc_3",
        ),
        fh.Script("new Tablesort(document.getElementById('cc_3'));"),
    )


def cc_d(args: Namespace, project: Project, scan: Scan):
    rows = query_cc(args, ReportLevel.DERIVED, project=project, scan=scan)

    t_head = fh.Tr(
        fh.Th("Entity Type", scope="col", style="text-align: left"),
        fh.Th("Value", scope="col", style="text-align: right"),
        fh.Th("Grade", scope="col", style="text-align: center"),
    )

    t_body = []
    for row in rows:
        t_row = fh.Tr(
            fh.Td(row.entity_type, style="text-align: left"),
            fh.Td(f"{row.cc_d.score:.1f}", style="text-align: right"),
            fh.Td(
                f"{row.cc_d.grade}",
                style=f"text-align: center; color: var(--pico-muted-color); background-color: {row.cc_d.color}",
            ),
        )
        t_body.append(t_row)

    return (
        fh.Table(
            fh.Thead(t_head),
            fh.Tbody(*t_body),
        ),
    )


def cc_h(args: Namespace, project: Project, scan: Scan = None):
    """Render our chart to display Radon CC information."""
    _, messages, transposed, _ = query_cc(args, ReportLevel.HISTORY, project=project, last=None)

    fig = go.Figure()
    for i, entity_type in enumerate(RadonCcEntityType):
        values_by_timestamp = transposed[entity_type.value]
        x_values = [datetime.fromisoformat(ts_) for ts_ in values_by_timestamp.keys()]
        y_values = [round(value, 2) for value in values_by_timestamp.values()]
        labels = custom_labels(f"({entity_type.plural})", messages, x_values, y_values)
        fig.add_trace(
            go.Scatter(
                x=x_values,
                y=y_values,
                customdata=labels,
                hovertemplate="%{customdata}",
                line_color=SERIES_COLORS[i % len(SERIES_COLORS)],
                marker_color=SERIES_COLORS[i % len(SERIES_COLORS)],
                mode="lines+markers",
                name=entity_type.plural,
            ),
        )

    style_figure(fig, layout={"yaxis_title": "Cyclomatic Complexity"})

    return fig.to_html().encode()
