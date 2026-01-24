"""Report data obo running 'fxtd' tool/script for level 1."""

from argparse import Namespace

from fasthtml import common as fh

from mq.tools.base import Scan
from mq.tools.fxtd.models import query


def fxtd_1(args: Namespace, scan: Scan):
    results = query(args, "1", scan=scan)
    grand_total = sum([result.count for result in results])

    t_head = fh.Tr(
        fh.Th("Type", scope="col", style="text-align: left"),
        fh.Th("Directory", scope="col", style="text-align: left"),
        fh.Th("Count", scope="col", style="text-align: right"),
    )

    t_body = []
    for result in results:
        t_row = fh.Tr(
            fh.Td(result.type, style="text-align: left"),
            fh.Td(result.directory, style="text-align: right"),
            fh.Td(f"{result.count:,d}", style="text-align: right"),
        )
        t_body.append(t_row)

    t_total = fh.Tr(
        fh.Td("TOTAL", style="text-align: left"),
        fh.Td(""),
        fh.Td(f"{grand_total:,d}", style="text-align: right"),
    )

    return (
        fh.Table(
            fh.Thead(t_head),
            fh.Tbody(*t_body),
            fh.Tfoot(t_total),
            id="fxtd_1",
        ),
        fh.Script("new Tablesort(document.getElementById('fxtd_1'));"),
    )
