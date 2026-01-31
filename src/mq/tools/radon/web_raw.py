"""Raw - Level 0."""

from argparse import Namespace
from datetime import datetime

from fasthtml import common as fh
from pygal import DateTimeLine
from pygal.style import Style

from mq.tools.base import Project, Scan
from mq.tools.radon.models import query_raw
from mq.web import DEFAULT_CHART_STYLE


def raw_0(args: Namespace, scan: Scan, project: Project = None):
    row = query_raw(args, "0", scan=scan)

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
            "Comments",
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
    rows, totals = query_raw(args, "1", scan)

    # fmt: off
    t_head = fh.Tr(
        fh.Th("Directory" , scope="col", style="text-align: left"),
        fh.Th("SLOC"      , scope="col", style="text-align: right"),
        fh.Th("Comments"  , scope="col", style="text-align: right"),
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
    rows = query_raw(args, "2", scan)

    # fmt: off
    t_head = fh.Tr(
        fh.Th("Directory" , scope="col", style="text-align: left"),
        fh.Th("File"      , scope="col", style="text-align: left"),
        fh.Th("SLOC"      , scope="col", style="text-align: right"),
        fh.Th("Comments"  , scope="col", style="text-align: right"),
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
    """Create Pygal chart."""
    timestamps, transposed, rocs, roc_gt = query_raw(args, "h", project=project, last=None)

    style = Style(**DEFAULT_CHART_STYLE)

    chart = DateTimeLine(
        y_title="Lines",
        dots_size=1,
        height=500,
        legend_at_bottom=True,
        legend_at_bottom_columns=3,
        style=style,
        tooltip_border_radius=10,
        x_label_rotation=45,  # Angle labels to prevent overlap
        x_labels_major_every=2,  # Show every other label
        x_value_formatter=lambda dt: dt.strftime("%Y-%m-%d %H:%M"),
    )

    for metric, dt_rows in transposed.items():
        datetime_values = [(datetime.fromisoformat(timestamp), value) for timestamp, value in dt_rows.items()]
        chart.add(metric.upper(), datetime_values)

    return chart.render()
