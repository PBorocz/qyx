"""CLI report rendering obo 'cloc' tool."""

from argparse import Namespace
from collections import defaultdict

from rich.tree import Tree
from rich import print

from mq.tools.base import Project, Request, Scan
from mq.utils import dt_to_display


def status(args: Namespace) -> None:
    """Use a simple terminal tree to display current db information."""
    tree = Tree("MQ Status")

    projects = Project.select()
    if args.name:
        projects = projects.where(Project.name == args.name)

    for project in projects:
        s_project = f"[red]PROJECT → {project.name}[/red]"
        if args.log_level != "info":
            s_project += f" [{project.id:3d}]"

        project_tree = tree.add(s_project)

        for request in Request.select().where(Request.project == project):
            source = request.arg_normalised if request.is_git else request.arg_raw
            s_request = f"[orange1]REQUEST[/orange1] [grey50]source='{source}'[/grey50]"
            if args.log_level != "info":
                s_request += f" [{request.id}] "
            scan_tree = project_tree.add(s_request)

            scans_for_request = Scan.select().order_by(Scan.as_of).where(Scan.request == request)
            if request.is_git and int(args.level) == 0:
                scan_tree = scan_tree_summary(args, request, scans_for_request, scan_tree)
            else:
                scan_tree = scan_tree_detailed(args, request, scans_for_request, scan_tree)

    if tree.children:
        print(tree)


def scan_tree_summary(args: Namespace, request, scans_for_request, scan_tree):
    dates_ = [scan.as_of for scan in scans_for_request]
    max_date, min_date = max(dates_), min(dates_)
    s_max_date, s_min_date = dt_to_display(max_date), dt_to_display(min_date)
    s_scans = (
        f"[bright_green]SCANS[/bright_green] {len(scans_for_request):,d} [grey50]{s_min_date} → {s_max_date}[/grey50]"
    )
    ta_tree = scan_tree.add(s_scans)

    # Count up the total number of scans by tool/analysis:
    counts = defaultdict(int)
    for scan in scans_for_request:
        s_analysis = scan.tool_analysis_display()
        counts[s_analysis] += 1
    for s_analysis, count in sorted(counts.items()):
        s_scan = f"[cyan]{s_analysis}[/cyan] → [green]{count:,d}[/green] scans"
        ta_tree.add(s_scan)

    return scan_tree


def scan_tree_detailed(args: Namespace, request, scans_for_request, scan_tree):
    for scan in scans_for_request:
        s_scan_count = _get_scan_count(args, scan)
        s_analysis = scan.tool_analysis_display()
        s_scan = (
            f"[bright_green]SCAN[/bright_green] → "
            f"[cyan]{s_analysis}[/cyan] "
            f"[green]{s_scan_count:4s}[/green] "
            f"[grey50]{dt_to_display(scan.as_of)}[/grey50]"
        )
        if args.log_level != "info":
            s_scan += f" [{scan.id}]"

        scan_tree.add(s_scan)


def _get_scan_count(args: Namespace, scan: Scan) -> str:
    """Return the scan's result count as a str already formatted for status tree."""
    tool_config = args.tools[scan.tool]
    model_class = tool_config.models[scan.analysis]
    count = model_class.filter(model_class.scan == scan).count()
    return f"{count:3d}"
