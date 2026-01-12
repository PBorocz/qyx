"""CC - Level 2."""

from fasthtml import common as fh

from mq.tools.base import Scan
from mq.tools.radon.models import query_cc


def cc_2(scan: Scan):
    plurals = dict(Function="Functions", Method="Methods", Class="Classes")
    rows = query_cc("2", scan=scan)

    # fmt: off
    t_head = fh.Tr(
        fh.Th("Directory"   , scope="col", style="text-align: left"),
        fh.Th("Filename"    , scope="col", style="text-align: left"),
        fh.Th("Entity Type" , scope="col", style="text-align: left"),
        fh.Th("Complexity"  , scope="col", style="text-align: right"),
        fh.Th("Rank"        , scope="col", style="text-align: center"),
    )
    # fmt: on

    t_body = []
    # fmt: off
    for row in rows:
        t_row = fh.Tr(
            fh.Td(row.directory                    , style="text-align: left"),
            fh.Td(row.filename                     , style="text-align: left"),
            fh.Td(plurals[row.entity_type]         , style="text-align: left"),
            fh.Td(f"{row.mean_complexity:.2f}"     , style="text-align: right"),
            fh.Td(row.get_rank(row.mean_complexity), style="text-align: center"),
        )
        t_body.append(t_row)
    # fmt: off

    return (
        fh.Table(
            fh.Thead(t_head),
            fh.Tbody(*t_body),
            fh.Tfoot(),
            id="cc_2",
        ),
        fh.Script("new Tablesort(document.getElementById('cc_2'));"),
    )
