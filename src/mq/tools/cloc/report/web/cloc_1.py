"""Report data obo running 'cloc' tool for level 1."""

from argparse import Namespace

from fasthtml import common as fh

from mq.tools.base import Scan
from mq.tools.cloc.models import query


def cloc_1(args: Namespace, scan: Scan):
    grand_total = query(args, "0", scan=scan)
    detail_rows = query(args, "1", scan=scan)

    t_head = fh.Tr(
        fh.Th("Directory", scope="col", style="text-align: left"),
        fh.Th("LOC", scope="col", style="text-align: right"),
        fh.Th("Comments", scope="col", style="text-align: right"),
        fh.Th("Blanks", scope="col", style="text-align: right"),
        fh.Th("TOTAL", scope="col", style="text-align: right"),
    )

    t_body = []
    for result in detail_rows:
        t_row = fh.Tr(
            fh.Td(result.directory, style="text-align: left"),
            fh.Td(f"{result.lines_code:,d}", style="text-align: right"),
            fh.Td(f"{result.lines_comment:,d}", style="text-align: right"),
            fh.Td(f"{result.lines_blank:,d}", style="text-align: right"),
            fh.Td(f"{result.lines_total:,d}", style="text-align: right"),
        )
        t_body.append(t_row)

    t_total = fh.Tr(
        fh.Td("TOTAL", style="text-align: left"),
        fh.Td(f"{grand_total.lines_code:,d}", style="text-align: right"),
        fh.Td(f"{grand_total.lines_comment:,d}", style="text-align: right"),
        fh.Td(f"{grand_total.lines_blank:,d}", style="text-align: right"),
        fh.Td(f"{grand_total.lines_total:,d}", style="text-align: right"),
    )

    return (
        fh.Table(
            fh.Thead(t_head),
            fh.Tbody(*t_body),
            fh.Tfoot(t_total),
            id="level_1",
        ),
        fh.Script("new Tablesort(document.getElementById('level_1'));"),
    )
