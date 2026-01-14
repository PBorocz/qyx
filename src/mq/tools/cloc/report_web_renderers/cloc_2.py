"""Report data obo running 'cloc' tool for level 2."""

from fasthtml import common as fh

from mq.tools.base import Scan
from mq.tools.cloc.models import query


def cloc_2(scan: Scan):
    results, column_totals, grand_total = query("2", scan=scan)

    t_head = fh.Tr(
        fh.Th("File", scope="col", style="text-align: left"),
        fh.Th("Lines of Code", scope="col", style="text-align: right"),
        fh.Th("Comment Lines", scope="col", style="text-align: right"),
        fh.Th("Blank Lines", scope="col", style="text-align: right"),
        fh.Th("TOTAL", scope="col", style="text-align: right"),
    )

    t_body = []
    for result in results:
        t_row = fh.Tr(
            fh.Td(f"{result.directory}/{result.filename}", style="text-align: left"),
            fh.Td(f"{result.lines_code:,d}", style="text-align: right"),
            fh.Td(f"{result.lines_comment:,d}", style="text-align: right"),
            fh.Td(f"{result.lines_blank:,d}", style="text-align: right"),
            fh.Td(f"{result.lines_total:,d}", style="text-align: right"),
        )
        t_body.append(t_row)

    t_total = fh.Tr(
        fh.Td("TOTAL", style="text-align: left"),
        fh.Td(f"{column_totals['lines_code']:.0f}", style="text-align: right"),
        fh.Td(f"{column_totals['lines_comment']:.0f}", style="text-align: right"),
        fh.Td(f"{column_totals['lines_blank']:.0f}", style="text-align: right"),
        fh.Td(f"{grand_total:.0f}", style="text-align: right"),
    )

    return (
        fh.Table(
            fh.Thead(t_head),
            fh.Tbody(*t_body),
            fh.Tfoot(t_total),
            id="level_2",
        ),
        fh.Script("new Tablesort(document.getElementById('level_2'));"),
    )
