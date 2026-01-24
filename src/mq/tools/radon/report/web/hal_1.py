"""HAL - Level 1."""

from argparse import Namespace

from fasthtml import common as fh

from mq.tools.base import Scan
from mq.tools.radon.models import query_hal, RadonHal


def hal_1(args: Namespace, scan: Scan):
    rows, mean_means = query_hal(args, "1", scan)

    t_tr = [fh.Th("Metric", scope="col", style="text-align: left")]
    for attr in RadonHal.attrs():
        t_tr.append(fh.Th(attr.display, scope="col", style="text-align: right"))
    t_head = fh.Tr(*t_tr)

    t_body = []
    for row in rows:
        t_row = [fh.Th(row.directory, style="text-align: left")]
        for attr in RadonHal.attrs():
            t_row.append(fh.Td(f"{getattr(row, attr.name):.2f}", style="text-align: right"))
        t_body.append(fh.Tr(*t_row))

    return (
        fh.Table(
            fh.Thead(*t_head),
            fh.Tbody(*t_body),
            id="hal_1",
        ),
        fh.Script("new Tablesort(document.getElementById('hal_1'));"),
    )
