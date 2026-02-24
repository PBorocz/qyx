"""Render the "home"/summary page."""

import logging
from argparse import Namespace

from bottle import request

from qyx.constants import ViewContext as vc
from qyx.tools.base import Project, Scan, State
from qyx.tools.cloc.web import cloc_0
from qyx.tools.fxtd.web import fxtd_0
from qyx.tools.radon.web import cc_0
from qyx.tools.radon.web import hal_0
from qyx.tools.radon.web import mi_0
from qyx.tools.radon.web import raw_0
from qyx.tools.ruff.web import ruff_0
from qyx.tools.ty.web import ty_0
from qyx.web import get_project_selector
from qyx.web.page import render_page, render_partial


log = logging.getLogger(__name__)


def render():
    project_options = get_project_selector()
    return render_page(
        "QYX Home",
        "base::pages/dashboard.html",
        project_options=project_options,
        set_project="/partials/set_project/_main_",
    )


def render_content(template: str = "base::fragments/body.htmx"):
    """Render the home/summary page."""
    args = request.app.args

    s_project_id = request.query.project
    project = Project.get_or_none(Project.id == int(s_project_id)) if s_project_id else None
    if not project:
        return render_partial("base::fragments/_no_project_yet.html")

    State.update(args, project=project.name)  # Remember for next instantiation!

    context = Namespace(as_of_dates={})
    context.analyses = []

    # FIXME: Can we make the following a bit more dynamic?
    scan_cloc = Scan.get_most_recent(project, "cloc", "cloc")
    if scan_cloc:
        context.cloc_0 = cloc_0(args, project, scan_cloc, context=vc.DASHBOARD)
        context.as_of_dates["cloc"] = scan_cloc.as_of_display(collapse_today=True)
        context.analyses.append(("cloc", "cloc"))

    scan_fxtd = Scan.get_most_recent(project, "fxtd", "fxtd")
    if scan_fxtd:
        context.fxtd_0 = fxtd_0(args, project, scan_fxtd, context=vc.DASHBOARD)
        context.as_of_dates["fxtd"] = scan_fxtd.as_of_display(collapse_today=True)
        context.analyses.append(("fxtd", "fxtd"))

    scan_ruff = Scan.get_most_recent(project, "ruff", "ruff")
    if scan_ruff:
        context.ruff_0 = ruff_0(args, project, scan_ruff, context=vc.DASHBOARD)
        context.as_of_dates["ruff"] = scan_ruff.as_of_display(collapse_today=True)
        context.analyses.append(("ruff", "ruff"))

    scan_ty = Scan.get_most_recent(project, "ty", "ty")
    if scan_ty:
        context.ty_0 = ty_0(args, project, scan_ty, context=vc.DASHBOARD)
        context.as_of_dates["ty"] = scan_ty.as_of_display(collapse_today=True)
        context.analyses.append(("ty", "ty"))

    scan_cc = Scan.get_most_recent(project, "radon", "cc")
    if scan_cc:
        context.cc_0 = cc_0(args, project, scan_cc, context=vc.DASHBOARD)
        context.as_of_dates["cc"] = scan_cc.as_of_display(collapse_today=True)
        context.analyses.append(("radon", "cc"))

    scan_hal = Scan.get_most_recent(project, "radon", "hal")
    if scan_hal:
        context.hal_0 = hal_0(args, project, scan_hal, context=vc.DASHBOARD)
        context.as_of_dates["hal"] = scan_hal.as_of_display(collapse_today=True)
        context.analyses.append(("radon", "hal"))

    scan_mi = Scan.get_most_recent(project, "radon", "mi")
    if scan_mi:
        context.mi_0 = mi_0(args, project, scan_mi, context=vc.DASHBOARD)
        context.as_of_dates["mi"] = scan_mi.as_of_display(collapse_today=True)
        context.analyses.append(("radon", "mi"))

    scan_raw = Scan.get_most_recent(project, "radon", "raw")
    if scan_raw:
        context.raw_0 = raw_0(args, project, scan_raw, context=vc.DASHBOARD)
        context.as_of_dates["raw"] = scan_raw.as_of_display(collapse_today=True)
        context.analyses.append(("radon", "raw"))

    return render_partial(template, **context.__dict__)
