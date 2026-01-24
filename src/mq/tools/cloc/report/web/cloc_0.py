"""Report data obo running 'cloc' tool for level 0."""

from argparse import Namespace

from fasthtml import common as fh

from mq.tools.base import Scan
from mq.tools.cloc.models import query


def cloc_0(args: Namespace, scan: Scan, **kwargs):
    results = query(args, "0", scan=scan)
    return (
        fh.Table(
            fh.Thead(
                fh.Tr(
                    fh.Th(
                        "LOC",
                        scope="col",
                        style="text-align: center",
                    ),
                    fh.Th(
                        "Comments",
                        scope="col",
                        style="text-align: center",
                    ),
                    fh.Th(
                        "Blanks",
                        scope="col",
                        style="text-align: center",
                    ),
                    fh.Th(
                        "TOTAL",
                        scope="col",
                        style="text-align: center",
                    ),
                ),
            ),
            fh.Tbody(
                fh.Tr(
                    fh.Td(
                        f"{results.lines_code:,d}",
                        " ",
                        fh.Small(f"({results.lines_code_p:.1f}%)"),
                        style="text-align: right",
                    ),
                    fh.Td(
                        f"{results.lines_comment:,d}",
                        " ",
                        fh.Small(f"({results.lines_comment_p:.1f}%)"),
                        style="text-align: right",
                    ),
                    fh.Td(
                        f"{results.lines_blank:,d}",
                        " ",
                        fh.Small(f"({results.lines_blank_p:.1f}%)"),
                        style="text-align: right",
                    ),
                    fh.Td(
                        fh.B(f"{results.lines_total:,d}"),
                        style="text-align: right",
                    ),
                ),
            ),
        ),
    )
