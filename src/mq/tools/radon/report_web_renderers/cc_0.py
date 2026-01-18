"""CC - Level 0."""

from fasthtml import common as fh

from mq.tools.base import Scan
from mq.tools.radon.models import query_cc


def cc_0(scan: Scan, **kwargs):
    plurals = dict(Function="Functions", Method="Methods", Class="Classes")
    rows = query_cc("0", scan=scan)

    # fmt: off
    t_head = fh.Tr(
        fh.Th("Entity Type"           , scope="col", style="text-align: left"),
        fh.Th("Cyclomatic Complexity" , scope="col", style="text-align: right"),
    )

    t_body = []
    for row in rows:
        t_row = fh.Tr(
            fh.Td(plurals[row.entity_type]    , style="text-align: left"),
            fh.Td(f"{row.mean_complexity:.1f}", style="text-align: right"),
        )
        t_body.append(t_row)
    # fmt: on

    return (
        fh.Table(
            fh.Thead(t_head),
            fh.Tbody(*t_body),
            fh.Tfoot(),
            id="cc_0",
        ),
        fh.Script("new Tablesort(document.getElementById('cc_0'));"),
    )
