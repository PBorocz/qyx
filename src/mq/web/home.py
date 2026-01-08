"""Render the "home"/summary page."""

from argparse import Namespace

from fasthtml import common as fh

from mq.tools.base import Project, Scan
from mq.tools.cloc.report_web_renderers.cloc_0 import cloc_0
from mq.tools.fxtd.report_web_renderers.fxtd_0 import fxtd_0
from mq.tools.radon.report_web_renderers.cc_0 import cc_0
from mq.tools.radon.report_web_renderers.hal_0 import hal_0
from mq.tools.radon.report_web_renderers.mi_0 import mi_0
from mq.tools.radon.report_web_renderers.raw_0 import raw_0
from mq.tools.ruff.report_web_renderers.ruff_0 import ruff_0
from mq.web.page import render_page


################################################################################################
# Page layout...
################################################################################################
def render(request):
    """Render the home/summary page."""
    args = request.app.state.args

    summaries = get_summaries(args)

    page_contents = []
    for project in Project.select():
        fh_details = (
            *summaries[(project.id, "cloc", "cloc")],
            fh.Hr(),
            *summaries[(project.id, "ruff", "ruff")],
            fh.Hr(),
            *summaries[(project.id, "radon", "mi")],
            fh.Hr(),
            *summaries[(project.id, "radon", "cc")],
            fh.Hr(),
            *summaries[(project.id, "radon", "hal")],
            fh.Hr(),
            *summaries[(project.id, "radon", "raw")],
            fh.Hr(),
            *summaries[(project.id, "fxtd", "fxtd")],
        )
        fh_section = fh.Section(
            fh.Details(
                fh.Summary(project.name),
                name="projects",
                open=True,
                *fh_details,
            ),
        )
        page_contents.append(fh_section)

    return render_page(
        request,
        "Home",
        "",
        fh.H1("Code Quality Data Dashboard"),
        fh.H3("Project Summaries"),
        *page_contents,
    )


def get_summaries(args: Namespace) -> dict:
    content = dict()
    for project in Project.select():
        # cloc:
        if scan := Scan.get_most_recent(project, "cloc", "cloc"):
            content[(project.id, "cloc", "cloc")] = cloc_0(args, scan)

        # ruff:
        if scan := Scan.get_most_recent(project, "ruff", "ruff"):
            content[(project.id, "ruff", "ruff")] = ruff_0(args, scan)

        # fxtd:
        if scan := Scan.get_most_recent(project, "fxtd", "fxtd"):
            content[(project.id, "fxtd", "fxtd")] = fxtd_0(args, scan)

        # ruff et al
        if scan := Scan.get_most_recent(project, "radon", "cc"):
            content[(project.id, "radon", "cc")] = cc_0(args, scan)

        if scan := Scan.get_most_recent(project, "radon", "hal"):
            content[(project.id, "radon", "hal")] = hal_0(args, scan)

        if scan := Scan.get_most_recent(project, "radon", "mi"):
            content[(project.id, "radon", "mi")] = mi_0(args, scan)

        if scan := Scan.get_most_recent(project, "radon", "raw"):
            content[(project.id, "radon", "raw")] = raw_0(args, scan)

    return content
