"""Render the "home"/summary page."""

import logging
from types import SimpleNamespace as Sns
from typing import Callable

from bottle import request

import qyx.constants as c
from qyx.tools._models_ import Project, Scan, State
from qyx.tools.common import import_method
from qyx.web.page import get_project_selector, render_page, render_template


log = logging.getLogger(__name__)


def dashboard_view(template: str = "base::dashboard_page.html") -> str:
    """Render the home/summary/Dashboard page."""
    project_options, _ = get_project_selector()
    return render_page("QYX Home", template, project_options=project_options)


def dashboard_view_content(template: str = "base::dashboard_body.html") -> str:
    """Supply the body portion of the Dashboard page on a project update."""
    args = request.app.args

    s_project_id = request.query.project
    project = Project.get_or_none(Project.id == int(s_project_id)) if s_project_id else None
    if not project:
        return render_template("base::_no_projects_yet.html")

    State.update(args, project=project.name)  # Remember for next instantiation!

    cards = []
    tool_context = {}
    for ta_ in args.config.get("renderers.web.dashboard.dimension_order", ()):
        tool, ingest_dimension = ta_, ta_
        if ":" in ta_:
            tool, ingest_dimension = (ta_.split(":") + [None])[:2]

        # Find the relevant scan
        scan = Scan.get_latest(project, tool, ingest_dimension=ingest_dimension)
        if not scan:
            log.debug(f"No Scan found for {tool=} {ingest_dimension=}")
            continue

        # Find the tool's level_0 web rendering method..
        method = _get_level_0_rendering_method(tool, ingest_dimension)

        # Determine the appropriate report_dimension to use to render the dashboard component.
        report_dimension = args.tools[tool].map_ingest_dimension_to_report_dimension(ingest_dimension)

        # Call it!
        # The return is tricky, we want to pass each tool's data/results at the TOP-level
        # to mimic what the underlying tools templates already expect.
        level = f"{ingest_dimension}_0"
        tool_context[level] = method(
            args=args,
            scan=scan,
            dimension=report_dimension,
            context=c.ViewContext.DASHBOARD,
        )

        # Define our dashboard "card"
        cards.append(
            Sns(
                tool=tool,
                ingest_dimension=ingest_dimension,
                template=f"{tool}::{level}.html",
                as_of_date=scan.as_of_display(collapse_today=True),
            ),
        )

    return render_template(template, cards=cards, **tool_context)


def _get_level_0_rendering_method(tool: str, ingest_dimension: str) -> Callable | None:
    """Lookup the appropriate *VIEW* method to use from the respective tool's web views."""
    # --> Relying upon NAMING CONVENTION's here!
    method = import_method(f"qyx.tools.{tool}.web:view_{ingest_dimension}_0")
    if method:
        return method

    # Some tools are simple enough that we don't need a dedicated web view method,
    # thus, directly call their respective level 0 MODEL-QUERY method.
    method = import_method(f"qyx.tools.{tool}.models:query_{ingest_dimension}_0")
    if method:
        return method

    # Well, then we're screwed.
    log.error(f"Unable to find level_0 rendering or query method for {tool=}:{ingest_dimension=}!")
    return None
