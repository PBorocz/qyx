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

from mq.web.routes.home import (
    page,
    partial_do_report,
    partial_module_selector,
    partial_report_selector,
    partial_run_selector,
)

log = logging.getLogger(__name__)

app, rt = fh.fast_app(debug=True)


def run_server(args: Namespace) -> None:
    """Run our web server."""
    if not args.no_browser:

        def __open_browser():
            """Start browser (ultimately in a background thread)."""
            log.info(f"Starting browser to https://localhost/{int(args.port)}")
            time.sleep(1)  # Wait for server to start
            webbrowser.open(f"http://localhost:{args.port}")

            threading.Thread(target=__open_browser, daemon=True).start()

    log.info(f"Starting server at https://localhost/{int(args.port)}")
    uvicorn.run(
        "mq.web.server:app",
        host="0.0.0.0",
        port=int(args.port),
        log_level="debug",
        access_log=True,
        use_colors=True,
        # reload=True,
    )


@rt
def index() -> Any:
    return page()


@rt
def modules(project: int = None) -> Any:
    return partial_module_selector(project)


@rt
def runs(project: int = None, module: str = "") -> Any:
    return partial_run_selector(project, module)


@rt
def reports(project: str, module: str, run_id: int) -> Any:
    return partial_report_selector(project, module, run_id)


@rt
def query(project: int, module: str, run_id: int, report: str) -> Any:
    return partial_do_report(project, module, run_id, report)


# Only necessary to diagnose issues when running server from within CLI.
# If so: % uv run python "src/mq/web/server.py"
if __name__ == "__main__":
    from mq import setup_sqlite

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--port", help="Optional port, default is 5011.", default=5011)
    parser.add_argument("--no-browser", action="store_true", help="Don't auto-open browser")
    args = parser.parse_args()
    setup_sqlite(args, logger)
    run_server(args)
