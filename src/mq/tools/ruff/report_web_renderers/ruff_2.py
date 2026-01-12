"""Report data obo running 'ruff' tool for level 2."""

from fasthtml import common as fh

from mq.tools.base import Scan
from mq.tools.ruff.models import query


def ruff_2(scan: Scan):
    rows = query("2", scan=scan)

    t_head = fh.Tr(
        fh.Th("Rule", scope="col", style="text-align: left"),
        fh.Th("File [line]", scope="col", style="text-align: left"),
        fh.Th("Message", scope="col", style="text-align: left"),
    )

    t_body = []
    for row in rows:
        t_row = fh.Tr(
            fh.Td(row.rule_code, style="text-align: left"),
            fh.Td(f"{row.directory}/{row.filename} [{row.line}]", style="text-align: left"),
            fh.Td(row.message, style="text-align: left"),
        )
        t_body.append(t_row)

    return (
        fh.Table(
            fh.Thead(t_head),
            fh.Tbody(*t_body),
            id="level_2",
        ),
        fh.Script("new Tablesort(document.getElementById('level_2'));"),
    )
