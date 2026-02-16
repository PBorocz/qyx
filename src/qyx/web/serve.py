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

from qyx.web.home import render_page_home

log = logging.getLogger(__name__)

app = None


def create_app(args):
    global app
    app = Bottle()

    # paths = [str(Path(__file__).parent / "templates")]
    # for tool_name, o_tool in args.tools.items():
    #     paths.append(f"src/qyx/tools/{tool_name}/templates")
    # args.jinja_env = Environment(loader=FileSystemLoader(paths), auto_reload=True)

    # Setup prefix-based templating based on both static and dynamic tool directories:
    loaders = dict(base=FileSystemLoader(str(Path(__file__).parent / "templates")))
    for tool_name, o_tool in args.tools.items():
        loaders[tool_name] = FileSystemLoader(f"src/qyx/tools/{tool_name}/templates")
    args.jinja_env = Environment(
        loader=PrefixLoader(loaders, delimiter="::"),
        auto_reload=True,
    )

    # Send our args into Bottle environment for availability across page renderers
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
    # Register routes (first static and then dynamic ones)
    ################################################################################
    app.route("/static/<filepath:path>")(serve_static)  # Love how easy THIS is!
    app.route("/about")(about)
    app.route("/")(render_page_home)
    for tool_name, o_tool in args.tools.items():
        app.route(f"/{tool_name}")(o_tool.render_web_method)
        if o_tool.render_web_module:  # Tools may not have web reporting setup yet!
            try:
                render_content_method: Callable = getattr(o_tool.render_web_module, "render_content")
                app.route(f"/partials/set_project/{tool_name}")(render_content_method)
            except AttributeError as exc:
                log.error(f"Expected to find 'render_content' in {tool_name}'s web.py module! ({exc})")
    if False:
        for route in app.routes:
            print(f"-{route.method:6s} {route.rule:30s} -> {route.callback.__module__}:{route.callback.__name__}")

    if args.browser:

        def __open_browser():
            """Start browser (using a background thread)."""
            log.info(f"Starting browser to https://localhost/{int(args.port)}")
            time.sleep(1)  # Wait for browser to start-up
            webbrowser.open(f"http://localhost:{args.port}")
            threading.Thread(target=__open_browser, daemon=True).start()

        __open_browser()

    ################################################################################
    # Start us up!
    ################################################################################
    log.info(f"Starting server at https://localhost/{int(args.port)}")
    app.run(
        host="localhost",
        port=int(args.port),
        debug=True,
        reloader=True,
    )


# def serve(args: Namespace) -> None:
#     """Run our web server."""
#     # Create our application and route instances..
#     global app, rt
#     app, rt = create_app(args)

#     # Register routes..
#     register(args, rt)

#     # And start us up!
#     if args.browser:

#         def __open_browser():
#             """Start browser (ultimately in a background thread)."""
#             log.info(f"Starting browser to https://localhost/{int(args.port)}")
#             time.sleep(1)  # Wait for server to start
#             webbrowser.open(f"http://localhost:{args.port}")
#             threading.Thread(target=__open_browser, daemon=True).start()

#         __open_browser()

#     log.info(f"Starting server at https://localhost/{int(args.port)}")
#     uvicorn.run(
#         app,
#         host="0.0.0.0",
#         port=int(args.port),
#         log_level="debug",
#         access_log=True,
#         use_colors=True,
#         # reload=True,
#     )


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
