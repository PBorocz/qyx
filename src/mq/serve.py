"""..."""

import argparse
import logging
import threading
import time
import webbrowser
from argparse import Namespace
from typing import Any

import uvicorn

from fasthtml import common as fh
from loguru import logger

from mq.modules import MODULES
from mq.modules.models import Project, Run
from mq.modules.cloc.models import query_history, query_summary
from mq.utilities import format_timestamp_headers

app, rt = fh.fast_app()

uvicorn_logger = logging.getLogger("uvicorn")


@rt("/")
def root() -> Any:
    projects = Project.select().order_by(Project.source_dir_relative)
    uvicorn_logger.info("This should show up")
    return fh.Titled(
        "Meta Quality",
        fh.Div(
            fh.H2("Installed Modules"),
            fh.Div(
                *[
                    fh.Label(
                        fh.Input(
                            type="radio",
                            name="module",
                            value=module,
                            hx_get="/runs",
                            hx_target="#run-selector",
                            hx_trigger="change",
                            hx_include="[name='project_id']",  # Include project in request
                        ),
                        f" {module.title()}",
                        cls="mr-4",
                    )
                    for module in MODULES
                ],
                cls="mb-4 grid grid-cols-auto gap-4",
            ),
            fh.H2("Project"),
            fh.Select(
                fh.Option("Select Project...", value="", selected=True),
                *[fh.Option(f"{project.source_dir_relative}", value=f"{project.id}") for project in projects],
                name="project_id",
                hx_get="/runs",
                hx_target="#run-selector",
                hx_trigger="change",
                hx_include="[name='module']",
            ),
            fh.Div(id="run-selector", cls="mt-4"),
            fh.Div(id="results", cls="mt-4"),
        ),
    )


@rt("/runs")
def get_runs(project_id: int = None, module: str = "") -> Any:
    if not project_id or not module:
        return fh.Div()

    runs = Run.select().where(Run.project_id == project_id, Run.module == module).order_by(Run.timestamp.desc())
    return fh.Div(
        fh.H3("Run Selection"),
        fh.Select(
            fh.Option("Select Run...", value="", selected=True),
            *[fh.Option(run.timestamp_display, value=run.id) for run in runs],
            name="run_id",
            hx_get="/query",
            hx_target="#results",
            hx_trigger="change",
            hx_include="[name='project_id']",
        ),
    )


@rt("/query")
def run_query(project_id: int, run_id: int) -> Any:
    project = Project.select().where(Project.id == project_id).get()
    uvicorn_logger.info("run_query")
    run = Run.select().where(Run.id == run_id).get()
    match run.module:
        case "cloc":
            return _render_cloc_history(project)
            # return _render_cloc_summary(run)
        case _:
            return fh.Div()


def _render_cloc_summary(run: Run) -> Any:
    results = query_summary(run)

    return fh.Div(
        fh.Table(
            fh.Thead(
                fh.Tr(
                    fh.Th("Code"),
                    fh.Th("Comments"),
                    fh.Th("Blanks"),
                ),
            ),
            fh.Tbody(
                fh.Tr(
                    fh.Td(f"{results.lines_code}"),
                    fh.Td(f"{results.lines_comment}"),
                    fh.Td(f"{results.lines_blank}"),
                ),
            ),
        ),
    )


def _render_cloc_history(project: Project) -> Any:
    timestamps, transposed, grand_totals = query_history(project)

    th_s = [fh.Th("Metric")]
    for i, header in enumerate(format_timestamp_headers(timestamps)):
        th_s.append(fh.Th(header))
    uvicorn_logger.info(f"{th_s=}")

    tr_s = []
    for metric, dt_rows in transposed.items():
        td_s = [fh.Td(metric)]
        for timestamp in timestamps:
            td_s.append(fh.Td(str(dt_rows[timestamp])))
        tr_s.append(fh.Tr(*td_s))

    return fh.Div(
        fh.H2("CLOC Results Over Time"),
        fh.Table(
            fh.Thead(fh.Tr(*th_s)),
            fh.Tbody(*tr_s),
        ),
    )


def run_server(args: Namespace) -> None:
    """Run our web server."""
    if not args.no_browser:

        def __open_browser():
            """Start browser (ultimately in a background thread)."""
            logger.info(f"Starting browser to https://localhost/{int(args.port)}")
            time.sleep(1)  # Wait for server to start
            webbrowser.open(f"http://localhost:{args.port}")

            threading.Thread(target=__open_browser, daemon=True).start()

    logger.info(f"Starting server at https://localhost/{int(args.port)}")
    print("here")
    uvicorn.run(
        "mq.serve:app",
        host="0.0.0.0",
        port=int(args.port),
        log_level="debug",
        access_log=True,
        use_colors=True,
    )


if __name__ == "__main__":
    from mq import setup_sqlite

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--port", help="Optional port, default is 5011.", default=5011)
    parser.add_argument("--no-browser", action="store_true", help="Don't auto-open browser")
    args = parser.parse_args()
    setup_sqlite(args, logger)
    run_server(args)
