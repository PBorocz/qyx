"""HAL - Level 2."""

from fasthtml import common as fh

from mq.tools.base import Scan
from mq.tools.radon.models import query_hal, RadonHal


def hal_2(scan: Scan):
    rows, _ = query_hal("2", scan)

    t_tr = [fh.Th("File", scope="col", style="text-align: left")]
    for attr in RadonHal.attrs():
        t_tr.append(fh.Th(attr.display, scope="col", style="text-align: right"))
    t_head = fh.Tr(*t_tr)

    t_body = []
    for row in rows:
        t_row = [fh.Th(f"{row.directory}/{row.filename}", style="text-align: left")]
        for attr in RadonHal.attrs():
            if attr.type == "float":
                s_value = f"{getattr(row, attr.name):.2f}"
            elif attr.type == "int":
                s_value = f"{getattr(row, attr.name):,d}"
            t_row.append(fh.Td(s_value, style="text-align: right"))
        t_body.append(fh.Tr(*t_row))

    return (
        fh.Table(
            fh.Thead(*t_head),
            fh.Tbody(*t_body),
            id="hal_2",
        ),
        fh.Script("new Tablesort(document.getElementById('hal_2'));"),
    )
