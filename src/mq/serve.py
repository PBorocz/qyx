"""..."""

import json
import sys
from argparse import Namespace

import uvicorn
from fasthtml import common as fh
from loguru import logger

from mq.modules import MODULES
from mq.modules.cloc.render import render_summary

app, rt = fh.fast_app()


@rt("/")
def get():
    print("- here in get...", file=sys.stderr, flush=True)
    return fh.Titled(
        "Meta Quality",
        fh.Div(
            fh.H2("Modules"),
            fh.Select(
                fh.Option("Select Module...", value="", selected=True),
                *[fh.Option(module, value=module) for module in MODULES],
                name="module_select",
                hx_get="/module-data",
                hx_target="#module-table",
                hx_trigger="change",
            ),
            fh.Div(id="module-table", cls="mt-4"),
            # Div(
            #     id="stats",
            #     hx_get="/stats-display",
            #     hx_trigger="every 60s",
            # ),
        ),
    )


@rt("/module-data")
def get_module_data(module_select: str = ""):
    match module_select:
        case "cloc":
            return _render_cloc_summary()
        case _:
            return ""


def _render_cloc_summary():
    # results = render_summary()
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
    return Pre(json.dumps(dict(last_run=None, total_processed=0, status="idle")))


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
