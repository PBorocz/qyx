"""CLI report rendering obo 'cloc' tool."""

from argparse import Namespace
from collections import defaultdict

from peewee import fn
from rich.console import Console
from rich.table import Table

from mq.modules.models import Project, Run


def status(args: Namespace) -> None:
    ################################################################################################
    # Query and transpose/aggregate
    ################################################################################################
    rows = (
        Run.select(Run, Project, fn.COUNT(Run.id).alias("run_count"))
        .join(Project)
        .group_by(Project.source_dir_relative, Run.module, Run.sub_module)
        .order_by(Project.source_dir_relative, Run.module, Run.sub_module)
    )
    # Transpose
    run_count_by_project_module = defaultdict(lambda: defaultdict(int))
    run_count_by_project = defaultdict(int)
    run_count_by_module = defaultdict(int)
    grand_total: int = 0
    module_sub_modules = set()
    for row in rows:
        module_sub_module = row.module if not row.sub_module else f"{row.module}/{row.sub_module}"
        module_sub_modules.add(module_sub_module)
        run_count_by_project_module[row.project_id.source_dir_relative][module_sub_module] = row.run_count
        run_count_by_project[row.project_id.source_dir_relative] += row.run_count
        run_count_by_module[module_sub_module] += row.run_count
        grand_total += row.run_count

    ################################################################################################
    # Report
    ################################################################################################
    # Only show the footer if we've gather across multiple projects..
    show_footer = True if len(run_count_by_project) > 1 else False

    # Render our summary status table.
    table = Table(
        title="MQ Status",
        title_justify="left",
        show_header=True,
        show_footer=show_footer,
        header_style="bold magenta",
    )
    table.add_column("Project", justify="right", footer="TOTAL")
    for module in sorted(module_sub_modules):
        table.add_column(module, justify="right", footer=f"{run_count_by_module[module]}")
    table.add_column("TOTAL", justify="right", footer=f"{grand_total}")

    for project, counts in run_count_by_project_module.items():
        row = [project]
        for module in sorted(module_sub_modules):
            row.append(f"{counts[module]}")
        row.append(f"{run_count_by_project[project]}")
        table.add_row(*row)

    Console().print(table)
