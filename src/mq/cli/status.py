"""CLI report rendering obo 'cloc' tool."""

from argparse import Namespace
from collections import defaultdict

from peewee import fn
from rich.tree import Tree
from rich import print

from mq.cli import cli_console, cli_table
from mq.modules.base import Project, Request, Scan
from mq.modules.cloc.models import Cloc


def status(args: Namespace) -> None:
    """Use a simple terminal tree to display current db contents."""
    tree = Tree("MQ Status")
    for project in Project.select():
        project_tree = tree.add(f"Project -> {project.name}")
        for request in Request.select().where(Request.project == project):
            sub_module = request.sub_module if request.sub_module else ""
            s_request = f"Request ->  {request.timestamp_display(full=True)} {request.module} {sub_module}"
            scan_tree = project_tree.add(s_request)
            for scan in Scan.select().where(Scan.request == request):
                sub_module = scan.sub_module if scan.sub_module else ""
                count = Cloc.filter(Cloc.scan == scan).count()
                s_scan = f"Scan -> {scan.timestamp_display(full=True)} {request.module} {sub_module} [{count} entries]"
                scan_tree.add(s_scan)
    print(tree)


def status_old(args: Namespace) -> None:
    ################################################################################################
    # Query and transpose/aggregate
    ################################################################################################
    # TODO: Implement args.project filtering!
    rows = (
        Scan.select(Scan, Project, fn.COUNT(Scan.id).alias("run_count"))
        .join(Project)
        .group_by(Project.input, Scan.module, Scan.sub_module)
        .order_by(Project.input, Scan.module, Scan.sub_module)
    )
    if not rows:
        cli_console.print('[yellow]No data is available, perform an [green]"mq ingest"[/green] first.[/yellow]')
        return

    # Transpose
    run_count_by_project_module = defaultdict(lambda: defaultdict(int))
    run_count_by_project = defaultdict(int)
    run_count_by_module = defaultdict(int)
    grand_total: int = 0
    module_sub_modules = set()
    for row in rows:
        s_project = row.project.name
        module_sub_module = row.module if not row.sub_module else f"{row.module}/{row.sub_module}"
        module_sub_modules.add(module_sub_module)
        run_count_by_project_module[s_project][module_sub_module] = row.run_count
        run_count_by_project[s_project] += row.run_count
        run_count_by_module[module_sub_module] += row.run_count
        grand_total += row.run_count

    ################################################################################################
    # Report
    ################################################################################################
    # Only show the footer if we've gather across multiple projects..
    show_footer = True if len(run_count_by_project) > 1 else False

    # Render our summary status table.
    table = cli_table(title="MQ Status", show_footer=show_footer)
    table.add_column("Project", justify="left", footer="TOTAL")
    for module in sorted(module_sub_modules):
        table.add_column(module, justify="right", footer=f"{run_count_by_module[module]}")
    table.add_column("TOTAL", justify="right", footer=f"{grand_total}")

    for project, counts in run_count_by_project_module.items():
        row = [project]
        for module in sorted(module_sub_modules):
            row.append(f"{counts[module]}")
        row.append(f"{run_count_by_project[project]}")
        table.add_row(*row)

    cli_console.print(table)
