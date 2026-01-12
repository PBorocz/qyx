"""Raw - Level 0."""

from fasthtml import common as fh

from mq.tools.base import Scan
from mq.tools.radon.models import query_raw


def raw_0(scan: Scan):
    rows = query_raw("0", scan=scan)

    # fmt: off
    t_head = fh.Tr(
        fh.Th("LLOC"            , scope="col", style="text-align: center"),
        fh.Th("SLOC"            , scope="col", style="text-align: center"),
        fh.Th("Comments"        , scope="col", style="text-align: center"),
        fh.Th("Multi"           , scope="col", style="text-align: center"),
        fh.Th("Blank"           , scope="col", style="text-align: center"),
        fh.Th("Single Comments" , scope="col", style="text-align: center"),
        fh.Th("Total"           , scope="col", style="text-align: center"),
    )
    # fmt: on

    t_body = []
    for row in rows:
        # fmt: off
        t_row = fh.Tr(
            fh.Td(f"{row.lloc:,}"            , style="text-align: center"),
            fh.Td(f"{row.sloc:,}"            , style="text-align: center"),
            fh.Td(f"{row.comments:,}"        , style="text-align: center"),
            fh.Td(f"{row.multi:,}"           , style="text-align: center"),
            fh.Td(f"{row.blank:,}"           , style="text-align: center"),
            fh.Td(f"{row.single_comments:,}" , style="text-align: center"),
            fh.Td(f"{row.loc:,}"             , style="text-align: center"),
        )
        # fmt: on
        t_body.append(t_row)

    return (
        fh.Table(
            fh.Thead(t_head),
            fh.Tbody(*t_body),
            fh.Tfoot(),
            id="raw_0",
        ),
        fh.Script("new Tablesort(document.getElementById('raw_0'));"),
    )
