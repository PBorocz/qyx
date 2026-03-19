"""..."""

import logging
import threading
import time
import webbrowser
from argparse import Namespace
from pathlib import Path

from bottle import Bottle
from bottle import static_file
from jinja2 import Environment, FileSystemLoader, PrefixLoader

from qyx.web.admin.status import status_page
from qyx.web.dashboard import dashboard_view, dashboard_view_content

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
    app.route("/")(dashboard_view)
    app.route("/content")(dashboard_view_content)

    # Admin - Project Status
    app.route("/admin/status")(status_page)

    ################################################################################
    # Dynamic routes for each individual tool that has web rendering available
    ################################################################################
    for o_tool in args.tools.tools():
        if not o_tool.render_web_module:  # Not every tool may have web reporting setup!
            continue

        # For tools with a "single" dimension:
        # ====================================
        # /<tool>          - home page - FULL page render
        # /<tool>/content  - change in which project is selected, show new body content (partial HTML
        #
        # For tools with a "multiple" dimensions:
        # =====================================
        # /<tool>           - home page - FULL page render
        # /<tool>/dimension - change in which project is selected,
        #                     cascade to update dimensions widget *AND* update body(partial HTML
        # /<tool>/content   - change in which dimension, show new body content (partial HTML.
        #
        paths_and_methods = [("", "view"), ("/content", "view_content")]
        if len(o_tool.dimensions) > 1:
            paths_and_methods.append(("/dimension", "view_dimension"))

        for path, method in paths_and_methods:
            _register_route(app, o_tool, path, method)

    if args.browser:
        _open_browser(args)

    ################################################################################
    # Start us up!
    ################################################################################
    app.run(host="localhost", port=int(args.port), debug=True, reloader=True)


def _register_route(app, o_tool, path, method) -> bool:
    try:
        method = getattr(o_tool.render_web_module, method)
    except AttributeError as exc:
        log.error(f"Tool '{o_tool.name}' missing method '{method}' in web.py module")
        log.debug(f"Full error: {exc}")
        return False

    route = f"/{o_tool.name}{path}"
    app.route(route)(method)
    log.debug(f"route='{route:20s}' → method='{method.__name__}'")
    return True


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
