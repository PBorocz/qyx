"""."""

import logging
from typing import Any

from fasthtml import ft

from mq.modules import MODULE_NAMES
from mq.modules.base import Project, Run

uvicorn_logger = logging.getLogger("uvicorn")


def page() -> Any:
    projects = Project.select().order_by(Project.path_input)
    return ft.Titled(
        "Meta Quality",
        ft.Div(
            ft.H3("Project"),
            ft.Select(
                ft.Option("Select Project...", value="", selected=True),
                *[ft.Option(f"{project.path_input}", value=f"{project.id}") for project in projects],
                name="project",
                hx_get="/modules",
                hx_target="#module-selector",
                hx_trigger="change",
            ),
            ft.Div(id="module-selector", cls="mt-4"),
            ft.Div(id="run-selector", cls="mt-4"),
            ft.Div(id="report-selector", cls="mt-4"),
            ft.Div(id="query", cls="mt-4"),
        ),
    )


def partial_module_selector(project: int = "") -> Any:
    return ft.Div(
        ft.H3("Module(s)"),
        ft.Div(
            *[
                ft.Label(
                    ft.Input(
                        type="radio",
                        name="module",
                        value=module,
                        hx_get="/runs",
                        hx_target="#run-selector",
                        hx_trigger="change",
                        hx_include="[name='project']",  # Include project in request.
                    ),
                    f" {module.title()}",
                    cls="mr-4",
                )
                for module in MODULE_NAMES
            ],
            cls="mb-4 grid grid-cols-auto gap-4",
        ),
    )


def partial_run_selector(project: int = "", module: str = "") -> Any:
    # uvicorn_logger.info(f"partial_run_selector {project=} {module=}")
    runs = Run.select().where(Run.project == project, Run.module == module).order_by(Run.timestamp.desc())
    return ft.Div(
        ft.H3("Run"),
        ft.Select(
            ft.Option("Select Run...", value="", selected=True),
            *[ft.Option(run.timestamp_display, value=run.id) for run in runs],
            name="run",
            hx_get="/reports",
            hx_target="#report-selector",
            hx_trigger="change",
            hx_include="[name='project'], [name='module']",
        ),
    )


def partial_report_selector(project: int, module: str, run_id: int) -> Any:
    # TODO: Make this sensitive to which reports are implemented by module
    # uvicorn_logger.info(f"partial_report_selector {project=} {module=} {run_id=}")
    reports = ("summary", "detail", "full", "history")
    return ft.Div(
        ft.H3("Reports Available"),
        ft.Div(
            *[
                ft.Label(
                    ft.Input(
                        type="radio",
                        name="report",
                        value=report,
                        hx_get="/query",
                        hx_target="#query",
                        hx_trigger="change",
                        hx_include="[name='project'], [name='module'], [name='run_id']",
                    ),
                    f" {report.title()}",
                    cls="mr-4",
                )
                for report in reports
            ],
            cls="mb-4 grid grid-cols-auto gap-4",
        ),
    )


def partial_do_report(project: int, module: str, run_id: int, report: str) -> Any:
    # uvicorn_logger.info(f"partial_query_results {project=} {module=} {run_id=} {report=}")
    run = Run.select().where(Run.id == run_id).get()
    project = Project.select().where(Project.id == run.project).get()
    # uvicorn_logger.info(f"partial_query_results {run.id=} {project.id=}")

    match run.module:
        case "cloc":
            from mq.modules.cloc import report_web

            match report:
                case "history":
                    return report_web.render_history(project)
                case "summary":
                    return report_web.render_summary(run)
                case "detail":
                    return report_web.render_detail(run)
                case "full":
                    return report_web.render_full(run)
                case _:
                    return ft.Div(ft.P(f"Sorry, we don't support {report=} yet!"))
        case _:
            return ft.Div(ft.P(f"Sorry, we haven't implemented reports yet for {module=}"))
