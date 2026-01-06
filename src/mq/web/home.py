"""Render the "home"/summary page."""

from argparse import Namespace

from fasthtml import common as fh

from mq.web.page import render_page
from mq.tools.base import Project, Scan
from mq.tools.cloc.report_web import render_level_0 as cloc_level_0
from mq.tools.ruff.report_web import render_level_0 as ruff_level_0
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

    content = get_content(args)

    page_content = (
        fh.Section(
            fh.Details(
                fh.Summary("A project Name"),
                name="projects",
                open=True,
                *(
                    fh.Section(*content[(1, "cloc", "cloc")], cls="bordered"),
                    fh.Section(*content[(1, "ruff", "ruff")], cls="bordered"),
                    fh.Section(*content[(1, "radon", "cc")], cls="bordered"),
                    fh.Section(*content[(1, "radon", "hal")], cls="bordered"),
                    fh.Section(*content[(1, "radon", "mi")], cls="bordered"),
                    fh.Section(*content[(1, "radon", "raw")], cls="bordered"),
                ),
                cls="bordered",
            ),
        ),
        fh.Section(
            fh.Details(
                fh.Summary("Another project Name"),
                name="projects",
                *(
                    *content[(1, "cloc", "cloc")],
                    *content[(1, "ruff", "ruff")],
                    *content[(1, "radon", "cc")],
                    *content[(1, "radon", "hal")],
                    *content[(1, "radon", "mi")],
                    *content[(1, "radon", "raw")],
                ),
            ),
            cls="bordered",
        ),
    )

    # for project in Project.select():
    #     project_sections = [fh.H3(project.name)]

    #     tools = []
    #     for tool_name, tool_config in args.tools.items():
    #         for analysis in tool_config.analyses:
    #             scan = Scan.get_most_recent(project, tool_name, analysis)
    #             tools.append(
    #                 fh.Details(fh.Summary(tool_name), open=True, *cloc_level_0(args, scan)),
    #             )

    # projects = [
    #     fh.Section(
    #         fh.Details(
    #             fh.Summary("Cloc"),
    #             open=True,
    #             *(
    #                 fh.Table(
    #                     fh.Thead(
    #                         fh.Tr(
    #                             fh.Th("Lines of Code", scope="col", style="text-align: right"),
    #                             fh.Th("Comment Lines", scope="col", style="text-align: right"),
    #                             fh.Th("Blank Lines", scope="col", style="text-align: right"),
    #                             fh.Th("TOTAL", scope="col", style="text-align: right"),
    #                         ),
    #                     ),
    #                     fh.Tbody(
    #                         fh.Tr(
    #                             fh.Td(f"{123:,d}", style="text-align: right"),
    #                             fh.Td(f"{234:,d}", style="text-align: right"),
    #                             fh.Td(f"{345:,d}", style="text-align: right"),
    #                             fh.Td(f"{456:,d}", style="text-align: right"),
    #                         ),
    #                     ),
    #                 ),
    #             ),
    #         ),
    #     ),
    # ]
    # for project, tool, analysis, scan in iterate_ptas(args):
    #     print(f"{project=} {tool=} {analysis=} {scan=}")
    #     projects.append(get_project(project))
    #     fh_section = fh.Section(
    #         fh.Details(fh.Summary("Summary"), name="details", open=True, *cloc_level_0(args, scan)),
    #     )
    # projects.append(fh_section)

    return render_page(
        request,
        "Home",
        "",
        fh.H1("Code Quality Data Dashboard"),
        fh.H3("Current Status"),
        *page_content,
    )


def get_content(args: Namespace) -> dict:
    content = dict()
    for project in Project.select():
        # cloc:
        if scan := Scan.get_most_recent(project, "cloc", "cloc"):
            content[(project.id, "cloc", "cloc")] = cloc_level_0(args, scan)

        # ruff:
        if scan := Scan.get_most_recent(project, "ruff", "ruff"):
            content[(project.id, "ruff", "ruff")] = ruff_level_0(args, scan)

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
