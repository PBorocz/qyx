"""Render the project status page."""

from types import SimpleNamespace as Sns

from qyx.web.page import render_page


################################################################################################
# Page layout...
################################################################################################
def status_page(template: str = "base::pages/status.html") -> str:
    """Render the page to display project status (non-interactive)."""
    ################################################################################
    # Needs to be rethought..what exactly do I want to see here???
    ################################################################################
    # for project in Project.select():
    #     for request in Request.select().where(Request.project == project):
    #         # Sum up the number of analysis scans done for this request
    #         query = Scan.select(
    #             Scan.

    #         print(request.id)

    context = Sns()
    context.rows = [
        Sns(date="2026-01-01", message="A message", cloc=4, ty=0),
        Sns(date="2026-01-02", message="Another message", cloc=3, ty=1),
    ]
    return render_page("QYX-Status", template, **context.__dict__)


################################################################################################
# def status_change_project(template: str = "base::fragments/status.htmx") -> str:
#     """Render the content portion (ie. body) of the page."""
#     args = bottle_request.app.args

#     s_project_id = bottle_request.query.project
#     project = Project.get_or_none(Project.id == int(s_project_id)) if s_project_id else None
#     if not project:
#         return render_partial("base::fragments/_no_project_yet.html")

# context = Sns(rows=[])
# for request in Request.select().where(Request.project == project):
#     for analysis in ("cloc", "ty"):
#         scan = Scan.get(Scan.request == request, Scan.analysis == analysis)
#         print(f"{scan.__dict__=}")

#     counts_by_scan_analysis = dict()
#     for scan in scans_for_request:
#         counts[scan.as_of] =
#         counts[scan.analysis] += 1

#     for analysis, count in sorted(counts.items()):
#         row = Sns(date=scan.as_of,
#                   message=scan.git_commit_message,

#         s_scan = f"[cyan]{s_analysis}[/cyan] → [green]{count:,d}[/green] scans"
#         ta_tree.add(s_scan)

# scan = Scan.get_most_recent(project, "ty", "ty")
# if not scan:
#     return render_partial("base::fragments/_no_scans_yet.html")

# State.update(args, project=project.name, analysis="ty")

# return render_partial(template, **context.__dict__)
