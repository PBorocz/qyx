"""MI - Level 2."""

from fasthtml import common as fh

from mq.tools.base import Scan
from mq.tools.radon.models import query_mi


def mi_2(scan: Scan):
    rows, _, _ = query_mi("2", scan)

    # fmt: off
    t_head = fh.Tr(
        fh.Th("Directory"            , scope="col", style="text-align: left"),
        fh.Th("Filename"             , scope="col", style="text-align: left"),
        fh.Th("Maintainability Index", scope="col", style="text-align: right"),
        fh.Th("Rank"                 , scope="col", style="text-align: center"),
    )

    t_body = []
    for row in rows:
        t_row = fh.Tr(
            fh.Td(row.directory   , style="text-align: left"),
            fh.Td(row.filename    , style="text-align: left"),
            fh.Td(f"{row.mi:.2f}" , style="text-align: right"),
            fh.Td(row.rank        , style="text-align: center"),
        )
        t_body.append(t_row)
    # fmt: on

    return (
        fh.Table(
            fh.Thead(*t_head),
            fh.Tbody(*t_body),
            id="mi_2",
        ),
        fh.Script("new Tablesort(document.getElementById('mi_2'));"),
    )
