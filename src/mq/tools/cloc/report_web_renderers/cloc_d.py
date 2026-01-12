"""Report data obo running 'cloc' tool for level d or derived data."""

from argparse import Namespace

from fasthtml import common as fh

from mq.tools.base import Scan
from mq.tools.cloc.models import query


def cloc_d(args: Namespace, scan: Scan):
    row = query(args, "d", scan=scan)
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
                    fh.Td(f"{row.lines_code:.2f}%", style="text-align: right"),
                    fh.Td(f"{row.lines_comment:.2f}%", style="text-align: right"),
                    fh.Td(f"{row.lines_blank:.2f}%", style="text-align: right"),
                    fh.Td(f"{row.lines_total:.2f}%", style="text-align: right"),
                ),
            ),
        ),
        fh.Table(
            fh.Thead(
                fh.Tr(
                    fh.Th("Metric", scope="col", style="text-align: left"),
                    fh.Th("Grade", scope="col", style="text-align: center"),
                    fh.Th("Value", scope="col", style="text-align: center"),
                ),
            ),
            fh.Tbody(
                fh.Tr(
                    fh.Td("Comment Ratio", style="text-align: left"),
                    fh.Td(
                        f"{row.comment_ratio.grade}",
                        style=f"text-align: center; color: var(--pico-muted-color); background-color: {row.comment_ratio.color}",
                    ),
                    fh.Td(f"{row.comment_ratio.score:.2f}", style="text-align: center;"),
                ),
                fh.Tr(
                    fh.Td("Code Density", style="text-align: left"),
                    fh.Td(
                        f"{row.code_density.grade}",
                        style=f"text-align: center; color: var(--pico-muted-color); background-color: {row.code_density.color}",
                    ),
                    fh.Td(f"{row.code_density.score:.2f}", style="text-align: center;"),
                ),
            ),
        ),
    )
