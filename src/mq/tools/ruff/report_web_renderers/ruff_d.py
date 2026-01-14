"""Report data obo running 'ruff' tool for level d or derived data."""

from fasthtml import common as fh

from mq.tools.base import Project, Scan
from mq.tools.ruff.models import query


def ruff_d(project: Project, scan: Scan):
    """Report on derived ruff metrics."""
    row = query("d", project=project, scan=scan)
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
                    fh.Td("Violations per kLOC (Simple)", style="text-align: left"),
                    fh.Td(
                        f"{row.violations_per_kloc.grade}",
                        style=f"text-align: center; color: var(--pico-muted-color); background-color: {row.violations_per_kloc.color}",
                    ),
                    fh.Td(f"{row.violations_per_kloc.score:.0f}", style="text-align: center;"),
                ),
                fh.Tr(
                    fh.Td("Violations per kLOC (Weighted)", style="text-align: left"),
                    fh.Td(
                        f"{row.weighted_violations_per_kloc.grade}",
                        style=f"text-align: center; color: var(--pico-muted-color); background-color: {row.weighted_violations_per_kloc.color}",
                    ),
                    fh.Td(f"{row.weighted_violations_per_kloc.score:.0f}", style="text-align: center;"),
                ),
            ),
        ),
    )
