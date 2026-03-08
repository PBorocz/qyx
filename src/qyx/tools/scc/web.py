"""Web rendering obo 'scc' tool."""

from types import SimpleNamespace as Sns

from bottle import request

from qyx.tools.base import Scan, State
from qyx.tools.scc.models import query_scc_0
from qyx.web.page import render, render_content


################################################################################################
# Routing/View methods
################################################################################################
def view(template: str = "scc::page.html") -> str:
    """View callback to render the entire tool page: project selector, analysis selector and body content."""
    o_tool = request.app.args.tools["scc"]
    return render(o_tool, template, get_content)


def view_content() -> str:
    """View callback for when a new analysis is selected, just need to update the body content directly."""
    o_tool = request.app.args.tools["scc"]
    project: str = request.query.project
    return render_content(project, o_tool, "scc", get_content)


################################################################################################
def get_content(scan: Scan) -> Sns:
    """Populate our tool's home page to the specified scan."""
    args = request.app.args
    State.update(args, project=scan.request.project.name, analysis=scan.analysis)

    context = Sns()
    context.scc_as_of = scan.as_of_display(collapse_today=True)
    context.scc_0 = query_scc_0(args, scan)
    # context.scc_1 = query_scc_1(args, scan)
    # context.scc_2 = query_scc_2(args, scan)
    # context.scc_f = view_scc_f(args, scan)
    # context.scc_h = view_scc_h(args, scan.request.project)
    return context
