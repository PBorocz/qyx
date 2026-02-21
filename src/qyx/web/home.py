"""Render the "home"/summary page."""

import logging
from argparse import Namespace

from bottle import request

from qyx.tools.base import Project, Scan, State
from qyx.tools.cloc.web import cloc_0, cloc_d
from qyx.tools.fxtd.web import fxtd_0
from qyx.tools.radon.web import cc_0, cc_d
from qyx.tools.radon.web import hal_0, hal_d
from qyx.tools.radon.web import mi_0, mi_d
from qyx.tools.radon.web import raw_0, raw_d
from qyx.tools.ruff.web import ruff_0, ruff_d
from qyx.tools.ty.web import ty_0, ty_d
from qyx.web import get_project_selector
from qyx.web.page import render_page, render_partial


log = logging.getLogger(__name__)


def render():
    project_options = get_project_selector()
    return render_page(
        "QYX Home",
        "base::pages/home.html",
        project_options=project_options,
        set_project="/partials/set_project/_main_",
    )


def render_content(template: str = "base::fragments/body.html"):
    """Render the home/summary page."""
    args = request.app.args

    s_project_id = request.query.project
    project = Project.get_or_none(Project.id == int(s_project_id)) if s_project_id else None
    if not project:
        return render_partial("base::fragments/_no_project_yet.html")

    State.update(args, project=project.name)  # Remember for next instantiation!

    context = Namespace(as_of_dates={})
    context.analyses = [
        ("cloc", "cloc"),
        ("fxtd", "fxtd"),
        ("ruff", "ruff"),
        ("ty", "ty"),
        ("radon", "raw"),
        ("radon", "cc"),
        ("radon", "mi"),
        ("radon", "hal"),
    ]

    # cloc:
    scan_cloc = Scan.get_most_recent(project, "cloc", "cloc")
    if scan_cloc:
        context.cloc_0 = cloc_0(args, project, scan_cloc)
        context.cloc_d = cloc_d(args, project, scan_cloc)
        context.as_of_dates["cloc"] = scan_cloc.as_of_display(collapse_today=True)

    scan_fxtd = Scan.get_most_recent(project, "fxtd", "fxtd")
    if scan_fxtd:
        context.fxtd_0 = fxtd_0(args, project, scan_fxtd)
        context.fxtd_d = None
        context.as_of_dates["fxtd"] = scan_fxtd.as_of_display(collapse_today=True)

    scan_ruff = Scan.get_most_recent(project, "ruff", "ruff")
    if scan_ruff:
        context.ruff_0 = ruff_0(args, project, scan_ruff)
        context.ruff_d = ruff_d(args, project, scan_ruff)
        context.as_of_dates["ruff"] = scan_ruff.as_of_display(collapse_today=True)

    scan_ty = Scan.get_most_recent(project, "ty", "ty")
    if scan_ty:
        context.ty_0 = ty_0(args, project, scan_ty)
        context.ty_d = ty_d(args, project, scan_ty)
        context.as_of_dates["ty"] = scan_ty.as_of_display(collapse_today=True)

    scan_cc = Scan.get_most_recent(project, "radon", "cc")
    if scan_cc:
        context.cc_0 = cc_0(args, project, scan_cc)
        context.cc_d = cc_d(args, project, scan_cc)
        context.as_of_dates["cc"] = scan_cc.as_of_display(collapse_today=True)

    scan_hal = Scan.get_most_recent(project, "radon", "hal")
    if scan_hal:
        context.hal_0 = hal_0(args, project, scan_hal)
        context.hal_d = hal_d(args, project, scan_hal)
        context.as_of_dates["hal"] = scan_hal.as_of_display(collapse_today=True)

    scan_mi = Scan.get_most_recent(project, "radon", "mi")
    if scan_mi:
        context.mi_0 = mi_0(args, project, scan_mi)
        context.mi_d = None
        context.as_of_dates["mi"] = scan_mi.as_of_display(collapse_today=True)

    scan_raw = Scan.get_most_recent(project, "radon", "raw")
    if scan_raw:
        context.raw_0 = raw_0(args, project, scan_raw)
        context.raw_d = None
        context.as_of_dates["raw"] = scan_raw.as_of_display(collapse_today=True)

    return render_partial(template, **context.__dict__)
