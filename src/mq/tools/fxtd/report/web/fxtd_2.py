"""Report data obo running 'fxtd' tool/script for level 2."""

from fasthtml import common as fh

from mq.tools.base import Scan
from mq.tools.fxtd.models import query


def fxtd_2(scan: Scan):
    rows = query("2", scan=scan)

    t_head = fh.Tr(
        fh.Th("Type", scope="col", style="text-align: center"),
        fh.Th("File [line]", scope="col", style="text-align: left"),
        fh.Th("Message", scope="col", style="text-align: left"),
    )

    t_body = []
    for row in rows:
        t_row = fh.Tr(
            fh.Td(row.type, style="text-align: center"),
            fh.Td(f"{row.directory}/{row.filename} [{row.line}]", style="text-align: left"),
            fh.Td(row.message, style="text-align: left"),
        )
        t_body.append(t_row)

    return (
        fh.Table(
            fh.Thead(t_head),
            fh.Tbody(*t_body),
            id="fxtd_2",
        ),
        fh.Script("new Tablesort(document.getElementById('fxtd_2'));"),
    )
