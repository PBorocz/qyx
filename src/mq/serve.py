"""..."""

import json
from argparse import Namespace

import uvicorn
from fasthtml import common as fh
from loguru import logger

from mq.modules import MODULES
from mq.modules.cloc.render import render_summary

app, rt = fh.fast_app()


@rt("/")
def get():
    return fh.Titled(
        "Meta Quality",
        fh.Div(
            fh.H2("Project Selection"),
            fh.Select(
                fh.Option("Select Project...", value="", selected=True),
                # TODO: populate with actual projects from database
                *[fh.Option(f"Project {i}", value=f"project_{i}") for i in range(1, 4)],
                name="project_select",
                hx_get="/runs",
                hx_target="#run-selector",
                hx_trigger="change",
            ),
            fh.Div(id="run-selector", cls="mt-4"),
            fh.Div(id="module-selector", cls="mt-4"),
            fh.Div(id="module-table", cls="mt-4"),
        ),
    )


@rt("/runs")
def get_runs(project_select: str = ""):
    if not project_select:
        return ""

    # TODO: Query database for runs based on project_select
    runs = [f"Run_{i}" for i in range(1, 5)]  # Mock data

    return fh.Div(
        fh.H3("Run Selection"),
        fh.Select(
            fh.Option("Select Run...", value="", selected=True),
            *[fh.Option(run, value=run) for run in runs],
            name="run_select",
            hx_get="/modules",
            hx_target="#module-selector",
            hx_trigger="change",
            hx_vals=f'{{"project_select": "{project_select}"}}',  # Pass project along
        ),
    )


@rt("/modules")
def get_modules(project_select: str = "", run_select: str = ""):
    if not project_select or not run_select:
        return ""

    return fh.Div(
        fh.H3("Module Selection"),
        fh.Select(
            fh.Option("Select Module...", value="", selected=True),
            *[fh.Option(module, value=module) for module in MODULES],
            name="module_select",
            hx_get="/module-data",
            hx_target="#module-table",
            hx_trigger="change",
            hx_vals=f'{{"project_select": "{project_select}", "run_select": "{run_select}"}}',
        ),
    )


@rt("/module-data")
def get_module_data(project_select: str = "", run_select: str = "", module_select: str = ""):
    match module_select:
        case "cloc":
            return _render_cloc_summary(project_select, run_select)
        case _:
            return ""


def _render_cloc_summary(project_select: str = "", run_select: str = ""):
    module_select = "cloc"
    # Replace with your actual data fetching logic
    return fh.Table(
        fh.Thead(fh.Tr(fh.Th("Column 1"), fh.Th("Column 2"))),
        fh.Tbody(
            fh.Tr(fh.Td(f"Data for {module_select}"), fh.Td("Some value")),
            fh.Tr(fh.Td(f"Data for {module_select}"), fh.Td("Some value")),
            fh.Tr(fh.Td(f"Data for {module_select}"), fh.Td("Some value")),
            fh.Tr(fh.Td(f"Data for {module_select}"), fh.Td("Some value")),
            fh.Tr(fh.Td(f"Data for {module_select}"), fh.Td("Some value")),
            fh.Tr(fh.Td(f"Data for {module_select}"), fh.Td("Some value")),
            fh.Tr(fh.Td(f"Data for {module_select}"), fh.Td("Some value")),
            fh.Tr(fh.Td(f"Data for {module_select}"), fh.Td("Some value")),
            fh.Tr(fh.Td(f"Data for {module_select}"), fh.Td("Some value")),
            # Add more rows as needed
        ),
        cls="table table-striped",  # Optional styling
    )


@rt("/stats-display")
def get():  # noqa: F811
    return fh.Pre(json.dumps(dict(last_run=None, total_processed=0, status="idle")))


def run_server(args: Namespace) -> None:
    """Run our web server."""
    logger.info(f"Starting server at https://localhost/{int(args.port)}")
    uvicorn.run(
        "mq.serve:app",
        host="0.0.0.0",
        port=int(args.port),
        # log_level="debug",
        # reload=True,
        # reload_dirs=["./src/mq"],
    )
    # serve(app, port=args.port, host="0.0.0.0")  # noqa: F405
