"""."""

import importlib
import logging
import types

from fasthtml import common as fh

from mq.web.page import render_page

log = logging.getLogger("uvicorn")
# log = logging.getLogger(__name__)


def register(args, rt):
    """Register all the routes for the app."""

    ################################################################################
    # Static routes...
    ################################################################################
    @rt("/")
    def get(request):
        return render_page(
            request,
            "Home",
            "Home",
            fh.H1("Code Quality Data Dashboard", cls="text-3xl font-bold mb-4"),
            fh.P("This is the home page. Use the navbar above to navigate.", cls="text-gray-600"),
        )

    @rt("/about")
    def about(request):
        return render_page(
            request,
            "About",
            "About",
            fh.H1("About Us", cls="text-3xl font-bold mb-4"),
            fh.P("Learn more about our application here.", cls="text-gray-600 mb-2"),
            fh.P("We build amazing things with FastHTML!", cls="text-gray-600"),
        )

    @rt("/contact")
    def contact(request):
        return render_page(
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

    @rt("/cloc_update-project")
    def cloc_update_project(request, project: str):
        """HTMX endpoint to update content based on project selection."""
        # Update your data fetching based on selected project
        # For now, just re-render with the project parameter
        from mq.tools.cloc.report_web import render_accordion_levels, render_history_chart

        return (
            *render_accordion_levels(request, project),
            *render_history_chart(request, project),
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
