"""Render the "home"/summary page."""

import logging
from argparse import Namespace
from types import SimpleNamespace as Sns
from typing import Callable

from bottle import request
from jinja2 import TemplateNotFound

import qyx.constants as c
from qyx.tools._models_ import Project, Scan, State, ToolType
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

    ################################################################################
    # We get a configuration from config.yaml like: <tool> or <tool>:<dimension>
    # where "dimension" could be either an ingest_dimension (like "raw" for radon) or
    # a report_dimension (like "file_churn" for ga).
    #
    # Gather all the cases:
    #
    # Case 1: ruff, cloc etc (SINGLE ingest_dimension and SINGLE report_dimension)
    #   scan_ingest_dimension        = <tool> (scan/ingest dimension defaults to <tool>)
    #   level_0 web rendering method = query_<tool>_0 (or view_<tool>_0 if available)
    #   context prefix               = <tool>_0
    #   level_0 template name        = <tool>::<tool>_0.html
    #
    # Case 2: scc, ga (SINGLE ingest_dimension and MULTIPLE report_dimensions)
    #   scan_ingest_dimension        = <tool> (scan/ingest dimension defaults to <tool>)
    #   level_0 web rendering method = query_<tool>_0 (or view_<tool>_0 if available)
    #   context prefix               = <tool>_0
    #   level_0 template name        = <tool>::<tool>_0.html
    #
    # Case 3: radon (MULTIPLE ingest_dimensions and corresponding MULTIPLE report_dimensions)
    #   scan_ingest_dimension        = <dimension>
    #   level_0 web rendering method = view_<dimension>_0 (or query_<dimension>_0 if view not available)
    #   context prefix               = <dimension>_0
    #   level_0 template name        = <tool>::<dimension>_0.html
    #
    ################################################################################

    cards = []
    tool_context = {}
    for ta_ in args.config.get("renderers.web.dashboard.dimension_order", ()):
        if ":" in ta_:
            tool, dimension = (ta_.split(":") + [None])[:2]
        else:
            tool, dimension = ta_, ta_
        o_tool = args.tools[tool]
        log.debug("--------------------")
        log.debug(f"{tool=} {dimension=}")

        ################################################################################
        # Find the relevant scan (we use 'ingest_by_dimension' to know how to query)
        ################################################################################
        if o_tool.ingest_by_dimension:
            if not (scan := Scan.get_latest(project, tool, ingest_dimension=dimension)):
                log.warning(f"No Scan found for {tool=}:{dimension=}")
                continue
        else:
            if not (scan := Scan.get_latest(project, tool)):
                log.warning(f"No Scan found for {tool=}")
                continue
        log.debug(f"{scan.id=}")

        ################################################################################
        # Find the tool's level_0 web rendering method..
        ################################################################################
        if not (method := _get_level_0_rendering_method(o_tool, dimension)):
            log.error(f"Unable to find level_0 rendering/query method for '{tool}:{dimension}'!")
            continue

        # Call it!
        # The return is tricky, we want to pass each tool's data/results at the TOP-level
        # to mimic what the underlying tools templates already expect.
        context_level = f"{dimension}_0" if o_tool.ingest_by_dimension else f"{o_tool.name}_0"
        log.debug(f"{context_level=}")
        tool_context[context_level] = method(
            args=args,
            scan=scan,
            dimension=dimension,
            context=c.ViewContext.DASHBOARD,
        )
        log.debug(f"{len(tool_context)=}")

        # Define our dashboard "card"
        if not (card_template := _get_level_0_template(args, o_tool, dimension)):
            log.error(f"Unable to find level_0 template for '{tool}:{dimension}'!")
            continue
        cards.append(
            Sns(
                tool=tool,
                dimension=dimension,
                template=card_template,
                as_of_date=scan.as_of_display(collapse_today=True),
            ),
        )

    import pprint as pp

    pp.pprint(cards)
    pp.pprint(tool_context)
    return render_template(template, cards=cards, **tool_context)


def _get_level_0_template(args: Namespace, o_tool: ToolType, dimension: str) -> str | None:
    if o_tool.ingest_by_dimension:
        template = f"{o_tool.name}::{dimension}_0.html"
    else:
        template = f"{o_tool.name}::{o_tool.name}_0.html"
    try:
        args.jinja_env.loader.get_source(args.jinja_env, template)
        return template
    except TemplateNotFound:
        pass
    return None


def _get_level_0_rendering_method(o_tool: ToolType, dimension: str) -> Callable | None:
    """Lookup the appropriate *VIEW* method to use from the respective tool's web views."""
    # --> Relying upon NAMING CONVENTION's here!
    if o_tool.ingest_by_dimension:
        # eg. Radon
        patterns = (
            f"qyx.tools.{o_tool.name}.web:view_{dimension}_0",
            f"qyx.tools.{o_tool.name}.models:query_{dimension}_0",
        )
    else:
        # eg. cloc, scc etc..
        patterns = (
            f"qyx.tools.{o_tool.name}.web:view_{o_tool.name}_0",
            f"qyx.tools.{o_tool.name}.models:query_{o_tool.name}_0",
        )

    for pattern in patterns:
        if method := import_method(pattern):
            log.debug(f"{o_tool.name=} {dimension=} {pattern=} {method.__name__=}")
            return method
    return None
