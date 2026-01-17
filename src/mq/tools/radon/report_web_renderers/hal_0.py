"""HAL - Level 0."""

from fasthtml import common as fh

from mq.tools.base import Scan
from mq.tools.radon.models import query_hal, RadonHal


def hal_0(scan: Scan, **kwargs):
    row = query_hal("0", scan=scan)

    # fmt: off
    t_head = fh.Tr(
        fh.Th("Metric", scope="col", style="text-align: left" ),
        fh.Th("Value" , scope="col", style="text-align: right"),
    )

    t_body = []
    for display, calc, attr, _ in RadonHal.attrs():
        t_row = fh.Tr(
            fh.Th(fh.Span(display), " ", fh.Small(calc), style="text-align: left" ),
            fh.Td(f"{getattr(row, attr):.2f}"     , style="text-align: right"),
        )
        t_body.append(t_row)
    # fmt: on

    return (
        fh.Table(
            fh.Thead(*t_head),
            fh.Tbody(*t_body),
            id="hal_0",
        ),
        fh.Script("new Tablesort(document.getElementById('hal_0'));"),
    )
