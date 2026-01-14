"""Report data obo running 'Radon-MI' tool for level d or derived data."""

from fasthtml import common as fh

from mq.tools.base import Project, Scan
from mq.tools.radon.models import query_mi


def mi_d(project: Project, scan: Scan):
    row = query_mi("d", project=project, scan=scan)
    return (
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
                    fh.Td("Maintainability", style="text-align: left"),
                    fh.Td(
                        f"{row.mi_d.grade}",
                        style=f"text-align: center; color: var(--pico-muted-color); background-color: {row.mi_d.color}",
                    ),
                    fh.Td(f"{row.mi_d.score:.0f}%", style="text-align: center;"),
                ),
            ),
        ),
    )
