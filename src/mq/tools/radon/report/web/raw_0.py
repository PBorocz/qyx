"""Raw - Level 0."""

from argparse import Namespace

from fasthtml import common as fh

from mq.tools.base import Scan
from mq.tools.radon.models import query_raw


def raw_0(args: Namespace, scan: Scan, **kwargs):
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
