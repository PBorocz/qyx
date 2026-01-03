"""CC - Level 3."""

from argparse import Namespace

from fasthtml import common as fh

from mq.tools.base import Scan
from mq.tools.radon.models import query_cc


def cc_3(args: Namespace, scan: Scan):
    rows = query_cc(args, "3", scan=scan)

    # fmt: off
    t_head = fh.Tr(
        fh.Th("Directory"   , scope="col", style="text-align: left"),
        fh.Th("Filename"    , scope="col", style="text-align: left"),
        fh.Th("Entity Name" , scope="col", style="text-align: left"),
        fh.Th("Entity Type" , scope="col", style="text-align: left"),
        fh.Th("Complexity"  , scope="col", style="text-align: right"),
        fh.Th("Rank"        , scope="col", style="text-align: center"),
    )
    # fmt: on

    t_body = []
    # fmt: off
    for row in rows:
        t_row = fh.Tr(
            fh.Td(row.directory           , style="text-align: left"),
            fh.Td(row.filename            , style="text-align: left"),
            fh.Td(row.entity_name         , style="text-align: left"),
            fh.Td(row.entity_type         , style="text-align: left"),
            fh.Td(f"{row.complexity:.2f}" , style="text-align: right"),
            fh.Td(row.rank                , style="text-align: center"),
        )
        t_body.append(t_row)
    # fmt: off

    return (
        fh.Table(
            fh.Thead(t_head),
            fh.Tbody(*t_body),
            fh.Tfoot(),
            id="cc_3",
        ),
        fh.Script("new Tablesort(document.getElementById('cc_3'));"),
    )
