"""Raw - Level 2."""

from fasthtml import common as fh

from mq.tools.base import Scan
from mq.tools.radon.models import query_raw


def raw_2(scan: Scan):
    rows = query_raw("2", scan)

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
