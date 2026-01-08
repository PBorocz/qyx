"""Render the "home"/summary page."""

from argparse import Namespace

from fasthtml import common as fh

from mq.web.page import render_page
from mq.tools.base import Project, Scan
from mq.tools.cloc.report_web import render_level_0 as cloc_level_0
from mq.tools.ruff.report_web import render_level_0 as ruff_level_0
from mq.tools.fxtd.report_web import render_level_0 as fxtd_level_0
from mq.tools.radon.report_web_renderers.cc_0 import cc_0
from mq.tools.radon.report_web_renderers.hal_0 import hal_0
from mq.tools.radon.report_web_renderers.mi_0 import mi_0
from mq.tools.radon.report_web_renderers.raw_0 import raw_0


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
            *summaries[(project.id, "ruff", "ruff")],
            *summaries[(project.id, "fxtd", "fxtd")],
            *summaries[(project.id, "radon", "cc")],
            *summaries[(project.id, "radon", "hal")],
            *summaries[(project.id, "radon", "mi")],
            *summaries[(project.id, "radon", "raw")],
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
            content[(project.id, "cloc", "cloc")] = cloc_level_0(args, scan)

        # ruff:
        if scan := Scan.get_most_recent(project, "ruff", "ruff"):
            content[(project.id, "ruff", "ruff")] = ruff_level_0(args, scan)

        # fxtd:
        if scan := Scan.get_most_recent(project, "fxtd", "fxtd"):
            content[(project.id, "fxtd", "fxtd")] = fxtd_level_0(args, scan)

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
