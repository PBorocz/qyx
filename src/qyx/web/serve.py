"""..."""

import logging
import threading
import time
import webbrowser
from argparse import Namespace
from pathlib import Path
from typing import Callable

from bottle import Bottle
from bottle import static_file
from jinja2 import Environment, FileSystemLoader, PrefixLoader

from qyx.web.admin.status import status_page
from qyx.web.dashboard import dashboard_page, dashboard_change_project

log = logging.getLogger(__name__)


def create_app(args):
    app = Bottle()

    # Setup prefix-based templating based on both static and dynamic tool directories:
    # (This gives us "name-space" control of templates, eg. "cloc::page/foo.html")
    loaders = dict(base=FileSystemLoader(str(Path(__file__).parent / "templates")))
    for o_tool in args.tools.tools():
        loaders[o_tool.name] = FileSystemLoader(f"src/qyx/tools/{o_tool.name}/templates")
    args.jinja_env = Environment(
        loader=PrefixLoader(loaders, delimiter="::"),
        auto_reload=True,
    )

    # Send our args into Bottle environment for availability across page routes
    app.args = args

    return app


def serve_static(filepath):
    return static_file(filepath, root="src/qyx/web/static")


def about():
    return "<H1>Welcome to QYX!</H1>"


def serve(args: Namespace) -> None:
    """Run our web server."""
    app = create_app(args)

    ################################################################################
    # Static routes
    ################################################################################
    app.route("/static/<filepath:path>")(serve_static)  # Love how easy THIS is!
    app.route("/admin/about")(about)

    # Home/Dashboard page
    app.route("/")(dashboard_page)
    app.route("/partials/set_project/_main_")(dashboard_change_project)

    # Admin - Project Status
    app.route("/admin/status")(status_page)

    ################################################################################
    # Dynamic routes for each individual tool that has web rendering available
    ################################################################################
    for o_tool in args.tools.tools():
        if not o_tool.render_web_module:  # Not every tool may have web reporting setup!
            continue

        # "Home" page for each tool:
        app.route(f"/{o_tool.name}")(o_tool.render_web_method)

        try:
            # HTMX callback page on a project (or analysis) change:
            render_content_method: Callable = getattr(o_tool.render_web_module, "render_content")
            app.route(f"/partials/set_project/{o_tool.name}")(render_content_method)
        except AttributeError as exc:
            log.error(f"Expected to find 'render_content' in {o_tool.name}'s web.py module! ({exc})")

    if args.browser:
        _open_browser()

    ################################################################################
    # Start us up!
    ################################################################################
    log.info(f"Starting server at https://localhost/{int(args.port)}")
    app.run(host="localhost", port=int(args.port), debug=True, reloader=True)


def _open_browser(args: Namespace):
    """Start browser (using a background thread)."""
    log.info(f"Starting browser to https://localhost/{int(args.port)}")
    time.sleep(1)  # Wait for browser to start-up
    webbrowser.open(f"http://localhost:{args.port}")
    threading.Thread(target=_open_browser, daemon=True).start()


# This is only necessary to diagnose issues when running server from within CLI.
# If so: % uv run python "src/qyx/web/serve.py"
if __name__ == "__main__":
    from qyx.setup.args_configuration import setup_configuration
    from qyx.setup.logging import setup_logging
    from qyx.setup.sqlite import setup_sqlite
    from qyx.setup.tools import setup_tools

    args = Namespace(log_level="warning", browser=False, port=5011)
    _, _, args.config = setup_configuration()
    setup_logging(args)
    setup_tools(args)
    setup_sqlite(args)
    serve(args)
