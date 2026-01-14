"""Report data obo running 'FXTD' tool for level d or derived data."""

from fasthtml import common as fh

from mq.tools.base import Project, Scan
from mq.tools.fxtd.models import query


def fxtd_d(project: Project, scan: Scan):
    rows = query("d", project=project, scan=scan)

    t_head = fh.Tr(
        fh.Th("Metric", scope="col", style="text-align: left"),
        fh.Th("Grade", scope="col", style="text-align: center"),
        fh.Th("Value", scope="col", style="text-align: right"),
    )

    t_body = []
    for row in rows:
        t_row = fh.Tr(
            fh.Td(f"{row.type}'s per KLOC", style="text-align: left"),
            fh.Td(
                f"{row.fxtd_d.grade}",
                style=f"text-align: center; color: var(--pico-muted-color); background-color: {row.fxtd_d.color}",
            ),
            fh.Td(f"{row.fxtd_d.score:.2f}", style="text-align: right"),
        )
        t_body.append(t_row)

    return (
        fh.Table(
            fh.Thead(t_head),
            fh.Tbody(*t_body),
        ),
    )
