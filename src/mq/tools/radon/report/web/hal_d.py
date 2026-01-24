"""Report data obo running 'Radon-HAL' tool for level d or derived data."""

from argparse import Namespace

from fasthtml import common as fh

from mq.tools.base import Project, Scan
from mq.tools.radon.models import query_hal


def hal_d(args: Namespace, project: Project, scan: Scan):
    row = query_hal(args, "d", project=project, scan=scan)
    print("here in hal_d")
    t_head = fh.Tr(
        fh.Th("Metric", scope="col", style="text-align: left"),
        fh.Th("Value", scope="col", style="text-align: right"),
        fh.Th("Grade", scope="col", style="text-align: center"),
    )

    t_body = (
        fh.Tr(
            fh.Td("Mean Bugs per kLOC", style="text-align: left"),
            fh.Td(f"{row.bugs_d.score:.1f}", style="text-align: right"),
            fh.Td(
                f"{row.bugs_d.grade}",
                style=f"text-align: center; color: var(--pico-muted-color); background-color: {row.bugs_d.color}",
            ),
        ),
        fh.Tr(
            fh.Td("Mean Difficulty", style="text-align: left"),
            fh.Td(f"{row.difficulty_d.score:.1f}", style="text-align: right"),
            fh.Td(
                f"{row.difficulty_d.grade}",
                style=f"text-align: center; color: var(--pico-muted-color); background-color: {row.difficulty_d.color}",
            ),
        ),
        fh.Tr(
            fh.Td("Mean Effort per LOC", style="text-align: left"),
            fh.Td(f"{row.effort_d.score:.1f}", style="text-align: right"),
            fh.Td(
                f"{row.effort_d.grade}",
                style=f"text-align: center; color: var(--pico-muted-color); background-color: {row.effort_d.color}",
            ),
        ),
        fh.Tr(
            fh.Td("Composite Score", style="text-align: left"),
            fh.Td(f"{row.composite_d.score:.1f}", style="text-align: right"),
            fh.Td(
                f"{row.composite_d.grade}",
                style=f"text-align: center; color: var(--pico-muted-color); background-color: {row.composite_d.color}",
            ),
        ),
    )

    return (
        fh.Table(
            fh.Thead(t_head),
            fh.Tbody(*t_body),
        ),
    )
