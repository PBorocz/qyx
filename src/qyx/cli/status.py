"""Report on status of projects, request and scans in db."""

from argparse import Namespace

from rich.tree import Tree
from rich import print

from qyx.constants import ALL_ITEMS, StatusLevel
from qyx.tools._models_ import Project, Request, Scan, ToolDimension, ToolType
from qyx.utils import dt_to_display


def status(args: Namespace) -> None:
    """Use a simple Rich terminal tree to display current db status summary."""
    tree = Tree("QYX Status")

    projects = Project.select()
    if args.name and args.name != ALL_ITEMS:
        projects = projects.where(Project.name == args.name)

    for project in projects:
        project_tree = tree.add(_get_project_name(args, project))

        for request in Request.select().where(Request.project == project):
            scan_tree = project_tree.add(_get_request_name(args, request))

            scans_for_request = Scan.select().order_by(Scan.as_of.desc()).where(Scan.request == request)
            if request.is_git and args.level == StatusLevel.GROUPED:
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
    scan_tree.add(s_scans)

    return scan_tree


def scan_tree_detailed(args: Namespace, request, scans_for_request, scan_tree):
    for scan in scans_for_request:
        s_scan = _get_scan_name(args, scan)
        scan_tree.add(s_scan)


def _get_project_name(args: Namespace, project: Project) -> str:
    s_project = f"[red]PROJECT → {project.name}[/red]"
    if args.log_level != "info":
        s_project += f" [{project.id:3d}]"
    return s_project


def _get_request_name(args: Namespace, request: Request) -> str:
    source = request.arg_normalised if request.is_git else request.arg_raw
    s_request = f"[orange1]REQUEST[/orange1] [grey50]source='{source}'[/grey50]"
    if args.log_level != "info":
        s_request += f" [{request.id}] "
    return s_request


def _get_scan_name(args: Namespace, scan: Scan) -> str:
    s_scan_count = _get_scan_count(args, scan)
    s_scan = (
        f"[bright_green]SCAN[/bright_green] → "
        f"[cyan]{scan.tool_dimension_display()}[/cyan] "
        f"[green]{s_scan_count:4s}[/green] "
        f"[grey50]{dt_to_display(scan.as_of)}[/grey50]"
    )
    if args.log_level != "info":
        s_scan += f" [{scan.id}]"
    return s_scan


def _get_scan_count(args: Namespace, scan: Scan) -> str:
    """Return the scan's result count as a str already formatted for status tree."""
    o_tool = args.tools[scan.tool]
    if o_tool.ingest_by_dimension:
        o_dimension = o_tool.find_dimension(scan.ingest_dimension)
        model_class = o_dimension.models[0]
    else:
        model_class = o_tool.dimensions[0].models[0]
    count = model_class.filter(model_class.scan == scan).count()
    return f"{count:3d}"
