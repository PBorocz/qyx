"""MI - Level 0."""

from fasthtml import common as fh

from mq.tools.base import Scan
from mq.tools.radon.models import query_mi


def mi_0(scan: Scan, **kwargs):
    row = query_mi("0", scan=scan)

    # fmt: off
    t_head = (
        fh.Th("Composite Maintainability",  style="text-align: left", colspan="2"),
    )
    t_body = (
        fh.Th("Score"             , style="text-align: left" ),
        fh.Th(f"{row.mi_mean:.2f}", style="text-align: right"),
    )
    # fmt: on

    return (
        fh.Table(fh.Thead(*t_head), fh.Tbody(*t_body), id="mi_0"),
        fh.Script("new Tablesort(document.getElementById('mi_0'));"),
    )
