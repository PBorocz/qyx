"""CLI report rendering obo 'cloc' tool."""

from argparse import Namespace

from peewee import InterfaceError
from rich.tree import Tree
from rich import print

from mq.tools.base import Project, Request, Scan
from mq.tools.cloc.models import Cloc
from mq.tools.fxtd.models import Fxtd
from mq.tools.radon.models import RadonCc, RadonHal, RadonMi, RadonRaw
from mq.tools.ruff.models import Ruff


def show_status(args: Namespace) -> None:
    """Use a simple terminal tree to display current db information."""
    tree = Tree("MQ Status")
    for project in Project.select():
        project_tree = tree.add(f"Project -> {project.name} [{project.id}]")

        for request in Request.select().where(Request.project == project):
            source = "from git" if request.from_git() else ""
            s_request = f"Request at {request.timestamp_display(full=True)} {source} [{request.id}]"
            scan_tree = project_tree.add(s_request)

            for scan in Scan.select().order_by(Scan.as_of).where(Scan.request == request):
                s_scan_count = _get_scan_count(scan)
                s_analysis = scan.tool_analysis_display()
                delimiter = "asOf" if request.from_git() else "@  "
                s_as_of_display = f"{delimiter} {scan.as_of_display(full=True)}"
                s_scan = f"Scan -> {s_analysis} {s_scan_count:4s} {s_as_of_display} [{scan.id}]"

                scan_tree.add(s_scan)

    if tree.children:
        print(tree)


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
        return ""
    else:
        return f"{count:3d}"
