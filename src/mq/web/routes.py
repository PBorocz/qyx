"""Primary routes for MQ app, static, partial and dynamically created."""

import logging
from datetime import datetime
from typing import Callable

from fasthtml import common as ft

from mq.web.home import render_page_home, render_partial_project_summary
from mq.utils.state import update_state

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
    for tool_name, tool_config in args.tools.items():
        # Create a closure to capture tool_name and tool_configuration
        def make_tool_route(name, tool_config):
            @rt(f"/{name}")
            def render_tool_page_method(request):
                render_method: Callable = tool_config.render_web_method
                return render_method(request, name, tool_config)

            return render_tool_page_method

        make_tool_route(tool_name, tool_config)

    @rt("/partials/set_project/_main_")
    def set_project_main(request, project: str):
        """HTMX endpoint to update content on the main/summary page based on updated project selection."""
        if project:
            update_state(last_project_id=project)
        return (*render_partial_project_summary(request, s_project_id=project),)

    @rt("/partials/set_project/{tool}")
    def set_project_tool(request, tool: str, project: str, analysis: str = None):
        """HTMX endpoint to update content on a "tool" page based on an updated project selection."""
        if not (tool_config := args.tools.get(tool)):
            return ft.Div(f"Unknown tool: {tool}", cls="error")

        try:
            # FIXME: Use what's already in tool_config instead of doing another import_component on every request.
            web_file_module = tool_config.import_component("web")
        except ImportError:
            return ft.Div(f"Couldn't find '{tool}/web.py' file!", cls="error")

        if project:
            update_state(last_project_id=project, last_tool=tool)

        return (*web_file_module.render_content(args, request, s_project_id=project, analysis=analysis),)
