"""Render the "home"/summary page."""

import importlib
import logging
from types import ModuleType
from types import SimpleNamespace as Sns
from typing import Callable

from bottle import request

from qyx.constants import ViewContext as Vc
from qyx.tools.base import Project, Scan, State

# from qyx.tools.cloc.models import query_0 as query_cloc_0
# from qyx.tools.fxtd.models import query_0 as query_fxtd_0
# from qyx.tools.radon.web import cc_0 as query_cc_0
# from qyx.tools.radon.web import hal_0 as query_hal_0
# from qyx.tools.radon.web import mi_0 as query_mi_0
# from qyx.tools.radon.web import raw_0 as query_raw_0
# from qyx.tools.ruff.models import query_0 as query_ruff_0
# from qyx.tools.ty.models import query_0 as query_ty_0
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

    context = Sns(as_of_dates={})
    context.analyses = []

    tool_analyses = args.config.get("renderers.web.dashboard.analysis_order", ())
    for ta_ in tool_analyses:
        (tool, analysis) = ta_.split(":")
        print(f"{tool=} {analysis=}", flush=True)

        scan = Scan.get_most_recent(project, tool, analysis)
        if scan:
            # Lookup the appropriate query method to use from the respective tool's models file.
            module: ModuleType = importlib.import_module(f"qyx.tools.{tool}.models")
            method_name: str = f"query_{analysis}_0"
            method: Callable = getattr(module, method_name)
            if method is None:
                log.error(f"Sorry, function {method_name} not found for {tool}:{analysis}")
                continue

            # Call it to populate our context..
            ctx = method(args, scan, context=Vc.DASHBOARD)
            setattr(context, f"{analysis}_0", ctx)
            context.as_of_dates[analysis] = scan.as_of_display(collapse_today=True)
            context.analyses.append((tool, analysis))

    # FIXME: Can we make the following a bit more dynamic?
    # scan_cloc = Scan.get_most_recent(project, "cloc", "cloc")
    # if scan_cloc:
    #     context.cloc_0 = query_cloc_0(scan_cloc, context=Vc.DASHBOARD)
    #     context.as_of_dates["cloc"] = scan_cloc.as_of_display(collapse_today=True)
    #     context.analyses.append(("cloc", "cloc"))

    # scan_fxtd = Scan.get_most_recent(project, "fxtd", "fxtd")
    # if scan_fxtd:
    #     context.fxtd_0 = query_fxtd_0(args, scan_fxtd, context=Vc.DASHBOARD)
    #     context.as_of_dates["fxtd"] = scan_fxtd.as_of_display(collapse_today=True)
    #     context.analyses.append(("fxtd", "fxtd"))

    # scan_ruff = Scan.get_most_recent(project, "ruff", "ruff")
    # if scan_ruff:
    #     context.ruff_0 = query_ruff_0(args, scan_ruff, context=Vc.DASHBOARD)
    #     context.as_of_dates["ruff"] = scan_ruff.as_of_display(collapse_today=True)
    #     context.analyses.append(("ruff", "ruff"))

    # scan_ty = Scan.get_most_recent(project, "ty", "ty")
    # if scan_ty:
    #     context.ty_0 = query_ty_0(args, scan_ty, context=Vc.DASHBOARD)
    #     context.as_of_dates["ty"] = scan_ty.as_of_display(collapse_today=True)
    #     context.analyses.append(("ty", "ty"))

    # scan_cc = Scan.get_most_recent(project, "radon", "cc")
    # if scan_cc:
    #     context.cc_0 = cc_0(args, scan_cc, context=Vc.DASHBOARD)
    #     context.as_of_dates["cc"] = scan_cc.as_of_display(collapse_today=True)
    #     context.analyses.append(("radon", "cc"))

    # scan_hal = Scan.get_most_recent(project, "radon", "hal")
    # if scan_hal:
    #     context.hal_0 = hal_0(args, scan_hal, context=Vc.DASHBOARD)
    #     context.as_of_dates["hal"] = scan_hal.as_of_display(collapse_today=True)
    #     context.analyses.append(("radon", "hal"))

    # scan_mi = Scan.get_most_recent(project, "radon", "mi")
    # if scan_mi:
    #     context.mi_0 = mi_0(args, scan_mi, context=Vc.DASHBOARD)
    #     context.as_of_dates["mi"] = scan_mi.as_of_display(collapse_today=True)
    #     context.analyses.append(("radon", "mi"))

    # scan_raw = Scan.get_most_recent(project, "radon", "raw")
    # if scan_raw:
    #     context.raw_0 = raw_0(args, scan_raw, context=Vc.DASHBOARD)
    #     context.as_of_dates["raw"] = scan_raw.as_of_display(collapse_today=True)
    #     context.analyses.append(("radon", "raw"))

    return render_template(template, **context.__dict__)
