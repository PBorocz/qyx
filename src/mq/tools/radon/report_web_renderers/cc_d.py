"""Report data obo running 'Radon-CC' tool for level d or derived data."""

from fasthtml import common as fh

from mq.tools.base import Project, Scan
from mq.tools.radon.models import query_cc


def cc_d(project: Project, scan: Scan):
    rows = query_cc("d", project=project, scan=scan)

    t_head = fh.Tr(
        fh.Th("Entity Type", scope="col", style="text-align: left"),
        fh.Th("Value", scope="col", style="text-align: right"),
        fh.Th("Grade", scope="col", style="text-align: center"),
    )

    t_body = []
    for row in rows:
        t_row = fh.Tr(
            fh.Td(row.entity_type, style="text-align: left"),
            fh.Td(f"{row.cc_d.score:.1f}", style="text-align: right"),
            fh.Td(
                f"{row.cc_d.grade}",
                style=f"text-align: center; color: var(--pico-muted-color); background-color: {row.cc_d.color}",
            ),
        )
        t_body.append(t_row)

    return (
        fh.Table(
            fh.Thead(t_head),
            fh.Tbody(*t_body),
        ),
    )
