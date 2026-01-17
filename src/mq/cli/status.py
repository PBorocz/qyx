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
        project_tree = tree.add(f"[red]Project[/red] [{project.id:3d}] → {project.name}")

        for request in Request.select().where(Request.project == project):
            source = request.arg_normalised if request.is_git else request.arg_raw
            timestamp = dt_to_display(request.timestamp, collapse_today=True)
            s_request = f"[blue]Request[/blue]  [{request.id:3d}] at {timestamp} from '{source}'"
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
    ta_tree = scan_tree.add(
        f"[bright_green]Scans[/bright_green] {len(scans_for_request):,d} {s_min_date} → {s_max_date}",
    )

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
        # delimiter = "asOf" if request.is_git else " at "
        # s_as_of_display = f"{delimiter} {dt_to_display(scan.as_of)}"
        s_scan = (
            f"[bright_green]Scan[/bright_green] [{scan.id:3d}] → "
            f"[cyan]{s_analysis}[/cyan] "
            f"[green]{s_scan_count:4s}[/green] "
            # f"[dim]{s_as_of_display}[/dim]"
        )
        scan_tree.add(s_scan)


def _get_scan_count(args: Namespace, scan: Scan) -> str:
    """Return the scan's result count as a str already formatted for status tree."""
    tool_config = args.tools[scan.tool]
    model_class = tool_config.models[scan.analysis]
    count = model_class.filter(model_class.scan == scan).count()
    if count == 0:
        return f"{'  -':3}"
    else:
        return f"{count:3d}"
