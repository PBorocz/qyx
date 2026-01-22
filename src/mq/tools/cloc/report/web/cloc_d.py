"""Report data obo running 'cloc' tool for level d or derived data."""

from fasthtml import common as fh

from mq.tools.base import Project, Scan
from mq.tools.cloc.models import query


def cloc_d(project: Project, scan: Scan):
    row = query("d", scan=scan)
    return (
        fh.Table(
            fh.Thead(
                fh.Tr(
                    fh.Th("Metric", scope="col", style="text-align: left"),
                    fh.Th("Value", scope="col", style="text-align: center"),
                    fh.Th("Grade", scope="col", style="text-align: center"),
                    fh.Th(fh.Small("Explanation"), scope="col", style="text-align: left;"),
                ),
            ),
            fh.Tbody(
                fh.Tr(
                    fh.Td("File Density", style="text-align: left"),
                    fh.Td(f"{row.avg_lines_per_file.score:.0f}", style="text-align: center;"),
                    fh.Td(
                        f"{row.avg_lines_per_file.grade}",
                        style="text-align: center; "
                        "color: var(--pico-muted-color); "
                        f"background-color: {row.avg_lines_per_file.color}",
                    ),
                    fh.Td(fh.Small("Average LoC per File"), style="text-align: left;"),
                ),
                fh.Tr(
                    fh.Td("Code Density", style="text-align: left"),
                    fh.Td(f"{row.code_density.score:.0f}%", style="text-align: center;"),
                    fh.Td(
                        f"{row.code_density.grade}",
                        style="text-align: center; "
                        "color: var(--pico-muted-color); "
                        f"background-color: {row.code_density.color}",
                    ),
                    fh.Td(fh.Small("LOC / (LOC + Blanks)"), style="text-align: left;"),
                ),
                fh.Tr(
                    fh.Td("Comment Ratio", style="text-align: left"),
                    fh.Td(f"{row.comment_ratio.score:.0f}%", style="text-align: center;"),
                    fh.Td(
                        f"{row.comment_ratio.grade}",
                        style="text-align: center; "
                        "color: var(--pico-muted-color); "
                        f"background-color: {row.comment_ratio.color}",
                    ),
                    fh.Td(fh.Small("Comments / (Comment + LOC)"), style="text-align: left;"),
                ),
            ),
        ),
    )
