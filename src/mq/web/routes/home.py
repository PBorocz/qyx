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
                # return page(
                #     request,
                #     name.title(),
                #     name.title(),
                #     fh.H1(f"{name.title()} Tool", cls="text-3xl font-bold mb-4"),
                #     fh.P(f"Configuration: {config}", cls="text-gray-600"),
                # )

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
        classes = "px-3 py-2 rounded-md text-sm font-medium"
        if active_page == name:
            classes += " bg-blue-600 text-white"
        else:
            classes += " text-gray-700 hover:bg-gray-200"
        nav_items.append(ft.A(name, href=path, cls=classes))

    return ft.Nav(
        ft.Div(
            ft.Div(
                ft.Span("MQ", cls="text-xl font-bold text-blue-600 mr-8"),
                *nav_items,
                cls="flex items-center space-x-2",
            ),
            cls="container mx-auto px-4",
        ),
        cls="bg-white shadow-md py-4",
    )


# Page layout wrapper
def page(request, title, active_page, *content):
    return ft.Html(
        ft.Head(
            ft.Title(title),
            # ft.Script(src="https://cdn.tailwindcss.com"),
            ft.Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css"),
        ),
        ft.Body(
            navbar(request, active_page),
            ft.Div(*content, cls="container mx-auto py-8"),  # px-4
        ),
    )
