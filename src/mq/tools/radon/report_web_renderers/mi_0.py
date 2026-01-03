"""MI - Level 0."""

from argparse import Namespace

from fasthtml import common as fh

from mq.tools.base import Scan
from mq.tools.radon.models import query_mi


def mi_0(args: Namespace, scan: Scan):
    row = query_mi(args, "0", scan=scan)

    # fmt: off
    t_body = (
        fh.Td("Composite Maintainability Score", style="text-align: left"),
        fh.Td(f"{row.mi_mean:.2f}"             , style="text-align: right"),
    )
    # fmt: on

    return (
        fh.Table(fh.Tbody(*t_body), id="mi_0"),
        fh.Script("new Tablesort(document.getElementById('mi_0'));"),
    )
