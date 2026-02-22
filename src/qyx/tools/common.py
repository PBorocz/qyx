"""Group together some common queries used across tools."""

from argparse import Namespace

from peewee import ModelSelect

from qyx.constants import ReportLevel as Rl
from qyx.tools.base import Project, Request, Scan


def get_loc(args: Namespace, project: Project) -> int | None:
    """Return the lines of code obo the specific Project (based on the most recent scans available)."""
    # We get LOC through either "cloc" and "Radon-Raw", try them both in order!
    from qyx.tools.cloc.models import query as query_cloc
    from qyx.tools.radon.models import query_raw

    cloc_scan = Scan.get_most_recent(project, "cloc", "cloc")
    if cloc_scan:
        result = query_cloc(args, Rl.SUMMARY, scan=cloc_scan)
        return result.lines_code

    radon_scan = Scan.get_most_recent(project, "radon", "raw")
    if radon_scan:
        result = query_raw(args, Rl.SUMMARY, project, radon_scan)
        return result.sloc

    return None


def get_scans_for_pta(project: Project, tool: str, analysis: str = None, last: int = None) -> ModelSelect:
    """Return the most recent scans for the selected project, tool and (maybe) analysis."""
    where = [
        Request.project == project,
        Scan.tool == tool,
    ]
    if analysis is not None:
        where.append(Scan.analysis == analysis)

    scans = Scan.select().where(*where).join(Request).order_by(Scan.as_of.desc())

    if last:
        scans = scans.limit(last)

    return scans
