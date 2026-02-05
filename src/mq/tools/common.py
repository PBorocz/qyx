"""Group together some common queries used across tools."""

from argparse import Namespace

from mq.constants import ReportLevel
from mq.tools.base import Project, Scan

from mq.tools.cloc.models import query as query_cloc
from mq.tools.radon.models import query_raw


def get_loc(args: Namespace, project: Project) -> int | None:
    """Return the lines of code obo the specific Project (based on the most recent scans available)."""
    # We get LOC through either "cloc" and "Radon-Raw", try them both in order!
    cloc_scan = Scan.get_most_recent(project, "cloc", "cloc")
    if cloc_scan:
        result = query_cloc(args, ReportLevel.SUMMARY, scan=cloc_scan)
        lines_of_code = result.lines_code
    else:
        radon_scan = Scan.get_most_recent(project, "radon", "raw")
        if radon_scan:
            result = query_raw(args, ReportLevel.SUMMARY, scan=radon_scan)
            lines_of_code = result.sloc
        else:
            lines_of_code = None

    return lines_of_code
