"""."""

import importlib
import logging
import types

from fasthtml import ft
from fasthtml import common as fh

log = logging.getLogger("uvicorn")
# log = logging.getLogger(__name__)


################################################################################################
# Define our routes..
################################################################################################
def register(args, rt):
    ################################################################################
    # Static routes...
    ################################################################################
    @rt("/")
    def get(request):
        return page(
            request,
            "Home",
            "Home",
            fh.H1("Code Quality Data Dashboard", cls="text-3xl font-bold mb-4"),
            fh.P("This is the home page. Use the navbar above to navigate.", cls="text-gray-600"),
        )

    @rt("/about")
    def about(request):
        return page(
            request,
            "About",
            "About",
            fh.H1("About Us", cls="text-3xl font-bold mb-4"),
            fh.P("Learn more about our application here.", cls="text-gray-600 mb-2"),
            fh.P("We build amazing things with FastHTML!", cls="text-gray-600"),
        )

    @rt("/contact")
    def contact(request):
        return page(
            request,
            "Contact",
            "Contact",
            fh.H1("Contact Us", cls="text-3xl font-bold mb-4"),
            fh.P("Get in touch with us:", cls="text-gray-600 mb-4"),
            fh.Ul(
                fh.Li("Email: hello@example.com"),
                fh.Li("Phone: (555) 123-4567"),
                cls="list-disc list-inside text-gray-600",
            ),
        )

    ################################################################################
    # Dynamic routes (ie. for each tool)
    ################################################################################
    for tool_name, tool_config in args.tools.items():
        # Create a closure to capture tool_name and tool_config
        def make_tool_route(name, config):
            @rt(f"/{name}")
            def render_tool_page_method(request):
                path_ = f"mq.tools.{name}.report_web"
                report_web: types.Module = importlib.import_module(path_)
                render_method = getattr(report_web, "render")
                return render_method(request, name, config)

            return render_tool_page_method

        make_tool_route(tool_name, tool_config)


# Helper function to create navbar with active state
def navbar(request, active_page):
    args = request.app.state.args  # Look through fasthtml app to get to "our" args..
    pages = [("Home", "/")]
    for tool_name, tool_config in args.tools.items():
        pages.append((tool_name.title(), f"/{tool_name}"))

    nav_items = []
    for name, path in pages:
        kwargs = dict(aria_current="page") if active_page == name else dict()
        nav_items.append(ft.A(name, href=path, **kwargs))

    return ft.Nav(
        ft.Ul(ft.Li(ft.Strong("MQ")), *[ft.Li(item) for item in nav_items]),  # Right-side nav..
        ft.Ul(),  # Left side nav..
        # ft.Ul(ft.Li(ft.Strong("MQ"))),
        # ft.Ul(*[ft.Li(item) for item in nav_items]),
    )


# Page layout wrapper
def page(request, title, active_page, *content):
    return ft.Html(
        ft.Head(
            ft.Title(f"MQ-{title}"),
            ft.Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css"),
            ft.Script(src="https://kozea.github.io/pygal.js/2.0.x/pygal-tooltips.min.js"),
        ),
        ft.Body(
            navbar(request, active_page),
            ft.Main(*content),
            cls="container",
        ),
    )
