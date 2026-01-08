"""Report data obo running 'cloc' tool for level 0."""

from argparse import Namespace

from fasthtml import common as fh

from mq.tools.base import Scan
from mq.tools.cloc.models import query


def cloc_0(args: Namespace, scan: Scan):
    results = query(args, "0", scan=scan)
    return (
        fh.Table(
            fh.Thead(
                fh.Tr(
                    fh.Th("Lines of Code", scope="col", style="text-align: right"),
                    fh.Th("Comment Lines", scope="col", style="text-align: right"),
                    fh.Th("Blank Lines", scope="col", style="text-align: right"),
                    fh.Th("TOTAL", scope="col", style="text-align: right"),
                ),
            ),
            fh.Tbody(
                fh.Tr(
                    fh.Td(f"{results.lines_code:,d}", style="text-align: right"),
                    fh.Td(f"{results.lines_comment:,d}", style="text-align: right"),
                    fh.Td(f"{results.lines_blank:,d}", style="text-align: right"),
                    fh.Td(f"{results.lines_total:,d}", style="text-align: right"),
                ),
            ),
        ),
    )
