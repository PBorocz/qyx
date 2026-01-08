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


def status(args: Namespace) -> None:
    """Use a simple terminal tree to display current db information."""
    tree = Tree("MQ Status")
    for project in Project.select():
        project_tree = tree.add(f"[red]Project[/red] [{project.id:3d}] → {project.name}")

        for request in Request.select().where(Request.project == project):
            source = request.arg_normalised if request.is_git else request.arg_raw
            timestamp = dt_to_display(request.timestamp, collapse_today=True)
            s_request = f"[blue]Request[/blue]  [{request.id:3d}] at {timestamp} from '{source}'"
            scan_tree = project_tree.add(s_request)

            scans_for_request = Scan.select().order_by(Scan.as_of).where(Scan.request == request)
            if request.is_git and int(args.level) == 0:
                scan_tree = scan_tree_summary(request, scans_for_request, scan_tree)
            else:
                scan_tree = scan_tree_detailed(request, scans_for_request, scan_tree)

    if tree.children:
        print(tree)


def scan_tree_summary(request, scans_for_request, scan_tree):
    dates_ = [scan.as_of for scan in scans_for_request]
    max_date, min_date = max(dates_), min(dates_)
    s_max_date, s_min_date = dt_to_display(max_date), dt_to_display(min_date)
    ta_tree = scan_tree.add(f"[bright_green]Scans[/bright_green] {s_min_date} → {s_max_date}")

    # Count up the total number of scans by tool/analysis:
    counts = defaultdict(int)
    for scan in scans_for_request:
        s_analysis = scan.tool_analysis_display()
        counts[s_analysis] += 1
    for s_analysis, count in sorted(counts.items()):
        s_scan = f"[cyan]{s_analysis.title()}[/cyan] → [green]{count:,d}[/green] scans"
        ta_tree.add(s_scan)

    return scan_tree


def scan_tree_detailed(request, scans_for_request, scan_tree):
    for scan in scans_for_request:
        s_scan_count = _get_scan_count(scan)
        s_analysis = scan.tool_analysis_display()
        delimiter = "asOf" if request.is_git else " at "
        s_as_of_display = f"{delimiter} {dt_to_display(scan.as_of)}"
        s_scan = (
            f"[bright_green]Scan[/bright_green] [{scan.id:3d}] → "
            f"[cyan]{s_analysis}[/cyan] "
            f"[green]{s_scan_count:4s}[/green] "
            f"[dim]{s_as_of_display}[/dim]"
        )
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
