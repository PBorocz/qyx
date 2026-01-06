"""CLI report rendering obo 'cloc' tool."""

from argparse import Namespace
from collections import defaultdict

from peewee import InterfaceError
from rich.tree import Tree
from rich import print

from mq.tools.base import Project, Request, Scan
from mq.tools.cloc.models import Cloc
from mq.tools.fxtd.models import Fxtd
from mq.tools.radon.models import RadonCc, RadonHal, RadonMi, RadonRaw
from mq.tools.ruff.models import Ruff
from mq.utils import dt_to_display


def show_status(args: Namespace) -> None:
    """Use a simple terminal tree to display current db information."""
    tree = Tree("MQ Status")
    for project in Project.select():
        project_tree = tree.add(f"Project -> {project.name} [{project.id}]")

        for request in Request.select().where(Request.project == project):
            source = request.git_repo if request.from_git() else project.input_path
            s_request = (
                f"Request  [{request.id:3d}] at {dt_to_display(request.timestamp, collapse_today=True)} from '{source}'"
            )
            scan_tree = project_tree.add(s_request)

            scans_for_request = Scan.select().order_by(Scan.as_of).where(Scan.request == request)
            if request.from_git() and int(args.level) == 0:
                scan_tree = scan_tree_summary(request, scans_for_request, scan_tree)
            else:
                scan_tree = scan_tree_detailed(request, scans_for_request, scan_tree)

    if tree.children:
        print(tree)


def scan_tree_summary(request, scans_for_request, scan_tree):
    total_requests = len(scans_for_request)

    dates_ = [scan.as_of for scan in scans_for_request]
    max_date, min_date = max(dates_), min(dates_)
    s_max_date, s_min_date = dt_to_display(max_date), dt_to_display(min_date)
    ta_tree = scan_tree.add(f"Scan -> {total_requests:,d} from {s_min_date} to {s_max_date}")

    # Count up the total number of scans by tool/analysis:
    counts = defaultdict(int)
    for scan in scans_for_request:
        s_analysis = scan.tool_analysis_display()
        counts[s_analysis] += 1
    for s_analysis, count in sorted(counts.items()):
        ta_tree.add(f"{s_analysis.title()} -> {count:,d} scans")

    return scan_tree


def scan_tree_detailed(request, scans_for_request, scan_tree):
    for scan in scans_for_request:
        s_scan_count = _get_scan_count(scan)
        s_analysis = scan.tool_analysis_display()
        delimiter = "asOf" if request.from_git() else " at "
        s_as_of_display = f"{delimiter} {dt_to_display(scan.as_of)}"
        s_scan = f"Scan [{scan.id:3d}] -> {s_analysis} {s_scan_count:4s} {s_as_of_display}"
        scan_tree.add(s_scan)


# FIXME: Make not as complex! ;-)
def _get_scan_count(scan: Scan) -> str:  # noqa: C901
    """Return the scan's result count as a str already formatted for status tree."""
    count = 0
    try:
        match scan.tool:
            # FIXME: Do this dynamically instead of hard-coding models?
            case "cloc":
                count = Cloc.filter(Cloc.scan == scan).count()
            case "fxtd":
                count = Fxtd.filter(Fxtd.scan == scan).count()
            case "ruff":
                count = Ruff.filter(Ruff.scan == scan).count()
            case "radon":
                match scan.analysis:
                    case "cc":
                        count = RadonCc.filter(RadonCc.scan == scan).count()
                    case "mi":
                        count = RadonMi.filter(RadonMi.scan == scan).count()
                    case "hal":
                        count = RadonHal.filter(RadonHal.scan == scan).count()
                    case "raw":
                        count = RadonRaw.filter(RadonRaw.scan == scan).count()
    except InterfaceError:
        return "?"
    if count == 0:
        return f"{'  -':3}"
    else:
        return f"{count:3d}"
