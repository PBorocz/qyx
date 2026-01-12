"""Report data obo running 'ruff' tool for level 0."""

from fasthtml import common as fh

from mq.tools.base import Scan

from mq.tools.ruff.models import query


def ruff_0(scan: Scan):
    row = query("0", scan=scan)
    return (
        fh.Table(
            fh.Tbody(
                fh.Tr(
                    fh.Th(fh.B("Ruff Issues"), style="text-align: left"),
                    fh.Td(fh.B(f"{int(row.count):,d}"), style="text-align: right"),
                ),
            ),
        ),
    )
