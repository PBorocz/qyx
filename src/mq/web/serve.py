"""..."""

import argparse
import logging
import threading
import time
import webbrowser
from argparse import Namespace

import uvicorn

from fasthtml import common as fh

import secrets

from mq.web.routes import register

log = logging.getLogger(__name__)

app, rt = None, None


def create_app(args):
    app, rt = fh.fast_app(
        debug=True,
        secret_key=secrets.token_hex(32),  # (using secret_key here allows us the ability to do session-based storage)
        static_path="src/mq/web/static",
    )

    # Send our args into the FastHtml environment for availability
    # within the various page renderers:
    app.state.args = args

    return app, rt


def serve(args: Namespace) -> None:
    """Run our web server."""
    # Create our application and route instances..
    global app, rt
    app, rt = create_app(args)

    # Register routes..
    register(args, rt)

    # And start us up!
    if args.browser:

        def __open_browser():
            """Start browser (ultimately in a background thread)."""
            log.info(f"Starting browser to https://localhost/{int(args.port)}")
            time.sleep(1)  # Wait for server to start
            webbrowser.open(f"http://localhost:{args.port}")
            threading.Thread(target=__open_browser, daemon=True).start()

        __open_browser()

    log.info(f"Starting server at https://localhost/{int(args.port)}")
    uvicorn.run(
        "mq.web.serve:app",
        host="0.0.0.0",
        port=int(args.port),
        log_level="debug",
        access_log=True,
        use_colors=True,
        # reload=True,
    )


# This is only necessary to diagnose issues when running server from within CLI.
# If so: % uv run python "src/mq/web/server.py"
if __name__ == "__main__":
    from mq import setup_sqlite

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--port", help="Optional port, default is 5011.", default=5011)
    parser.add_argument("--browser", action="store_true", help="Auto-open browser", default=False)
    args = parser.parse_args()
    setup_sqlite(args)
    serve(args)


# @rt
# def index() -> Any:
#     return page()


# @rt
# def modules(project: int = None) -> Any:
#     return partial_module_selector(project)


# @rt
# def runs(project: int = None, module: str = "") -> Any:
#     return partial_run_selector(project, module)


# @rt
# def reports(project: str, module: str, run_id: int) -> Any:
#     return partial_report_selector(project, module, run_id)


# @rt
# def query(project: int, module: str, run_id: int, report: str) -> Any:
#     return partial_do_report(project, module, run_id, report)
