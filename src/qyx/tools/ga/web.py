"""Render web data obo running 'ga' tool."""

from argparse import Namespace

from types import SimpleNamespace as Sns

from bottle import request

from qyx.constants import ViewContext as Vc
from qyx.tools._models_ import Scan, State
from qyx.tools.ga.models import query_ga_0
from qyx.web.page import render, render_content, render_dimensions
# from qyx.web.plotly import SERIES_COLORS, custom_labels, style_figure


################################################################################################
# Routing/View methods
################################################################################################
def view(template: str = "ga::page.html") -> str:
    """View callback to render the entire tool page: project selector, dimension selector and body content."""
    o_tool = request.app.args.tools["ga"]
    return render(o_tool, template, get_content)


def view_dimension() -> str:
    """View callback when project changes: Render BOTH updated dimension selector *AND* fresh body on an OOB basis."""
    o_tool = request.app.args.tools["ga"]
    project: str = request.query.project
    return render_dimensions(o_tool, project, get_content)


def view_content() -> str:
    """View callback for when a new dimension is selected, just need to update the body content directly."""
    o_tool = request.app.args.tools["ga"]
    project: str = request.query.project
    return render_content(project, o_tool, request.query.dimension, get_content)


################################################################################################
def get_content(scan: Scan, dimension: str) -> Sns:
    """Populate our tool's home page to the specified scan."""
    args = request.app.args

    State.update(args, project=scan.request.project.name, dimension=dimension)

    context = Sns()
    context.ga_as_of = scan.as_of_display(collapse_today=True)
    context.ga_0 = view_ga_0(args, scan, dimension)
    return context


def view_ga_0(args: Namespace, scan: Scan, dimension: str, context: Vc = Vc.TOOL_HOME) -> list:
    result = query_ga_0(args, scan, dimension)
    if context == Vc.DASHBOARD:
        # Don't display as many entries on the dashboard
        setattr(result, dimension, getattr(result, dimension)[0:10])
    return result
