"""HAL - Level 3."""

from argparse import Namespace

from fasthtml import common as fh

from mq.tools.base import Scan
from mq.tools.radon.models import query_hal, RadonHal


def hal_3(args: Namespace, scan: Scan):
    rows, _ = query_hal(args, "3", scan)

    t_tr = [
        fh.Th("File", scope="col", style="text-align: left"),
        fh.Th("Name", scope="col", style="text-align: left"),
    ]
    for display, attr, _ in RadonHal.attrs():
        t_tr.append(fh.Th(display, scope="col", style="text-align: right"))
    t_head = fh.Tr(*t_tr)

    t_body = []
    for row in rows:
        t_row = [
            fh.Td(f"{row.directory}/{row.filename}", style="text-align: left"),
            fh.Td(row.name, style="text-align: left"),
        ]
        for _, attr, fmt in RadonHal.attrs():
            if fmt == "float":
                s_value = f"{getattr(row, attr):.3f}"
            elif fmt == "int":
                s_value = f"{getattr(row, attr):,d}"
            t_row.append(fh.Td(s_value, style="text-align: right"))
        t_body.append(fh.Tr(*t_row))

    return (
        fh.Table(
            fh.Thead(*t_head),
            fh.Tbody(*t_body),
            id="hal_3",
        ),
        fh.Script("new Tablesort(document.getElementById('hal_3'));"),
    )
