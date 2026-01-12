"""MI - Level 1."""

from fasthtml import common as fh

from mq.tools.base import Scan
from mq.tools.radon.models import query_mi


def mi_1(scan: Scan):
    rows, _, _, _ = query_mi("1", scan)

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
