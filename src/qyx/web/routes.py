"""Primary routes for application's static, partial and dynamically created URL's."""

import logging
from datetime import datetime
from typing import Callable

from fasthtml import common as ft

from qyx.web.home import render_page_home, render_partial_project_summary

log = logging.getLogger("uvicorn")


def register(args, rt):  # noqa: C901
    """Register all the routes for the app."""

    ################################################################################
    # Static routes...
    ################################################################################
    @rt("/")
    def get_index(request):
        return render_page_home(request)

    @rt("/health")
    def get_health(request):
        return datetime.now().isoformat()

    # @rt("/about")
    # def about(request):
    #     return render_home(
    #         request,
    #         "About",
    #         "About",
    #         ft.H1("About Us", cls="text-3xl font-bold mb-4"),
    #         ft.P("Learn more about our application here.", cls="text-gray-600 mb-2"),
    #         ft.P("We build amazing things with FastHTML!", cls="text-gray-600"),
    #     )

    # @rt("/contact")
    # def contact(request):
    #     return render_page(
    #         request,
    #         "Contact",
    #         "Contact",
    #         ft.H1("Contact Us", cls="text-3xl font-bold mb-4"),
    #         ft.P("Get in touch with us:", cls="text-gray-600 mb-4"),
    #         ft.Ul(
    #             ft.Li("Email: hello@example.com"),
    #             ft.Li("Phone: (555) 123-4567"),
    #             cls="list-disc list-inside text-gray-600",
    #         ),
    #     )

    ################################################################################
    # Dynamic routes (ie. for each tool)
    ################################################################################
    for tool_name, o_tool in args.tools.items():
        # Create a closure to capture tool_name and o_tooluration
        def make_tool_route(name, o_tool):
            @rt(f"/{name}")
            def render_tool_page_method(request):
                render_method: Callable = o_tool.render_web_method
                return render_method(request, name, o_tool)

            return render_tool_page_method

        make_tool_route(tool_name, o_tool)

    @rt("/partials/set_project/_main_")
    def set_project_main(request, project: str):
        """HTMX endpoint to update content on the main/summary page based on updated project selection."""
        return (*render_partial_project_summary(request, s_project_id=project),)

    @rt("/partials/set_project/{tool}")
    def set_project_tool(request, tool: str, project: str, analysis: str = None):
        """HTMX endpoint to update content on a "tool" page based on an updated project selection."""
        o_tool = args.tools[tool]
        try:
            render_content_method: Callable = getattr(o_tool.render_web_module, "render_content")
        except AttributeError:
            return ft.Div(f"Sorry, unable to render_content obo '{tool}'!", cls="error")

        return (*render_content_method(args, request, s_project_id=project, analysis=analysis),)
