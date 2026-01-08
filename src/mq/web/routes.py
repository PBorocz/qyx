"""Primary routes for MQ app, static, partial and dynamically created."""

import importlib
import logging
import types

from fasthtml import common as ft

from mq.web.home import render as render_home

log = logging.getLogger("uvicorn")


def register(args, rt):
    """Register all the routes for the app."""

    ################################################################################
    # Static routes...
    ################################################################################
    @rt("/")
    def get(request):
        return render_home(request)

    # @rt("/about")
    # def about(request):
    #     return render_page(
    #         request,
    #         "About",
    #         "About",
    #         fh.H1("About Us", cls="text-3xl font-bold mb-4"),
    #         fh.P("Learn more about our application here.", cls="text-gray-600 mb-2"),
    #         fh.P("We build amazing things with FastHTML!", cls="text-gray-600"),
    #     )

    # @rt("/contact")
    # def contact(request):
    #     return render_page(
    #         request,
    #         "Contact",
    #         "Contact",
    #         fh.H1("Contact Us", cls="text-3xl font-bold mb-4"),
    #         fh.P("Get in touch with us:", cls="text-gray-600 mb-4"),
    #         fh.Ul(
    #             fh.Li("Email: hello@example.com"),
    #             fh.Li("Phone: (555) 123-4567"),
    #             cls="list-disc list-inside text-gray-600",
    #         ),
    #     )

    @rt("/partials/new_project/{tool}")
    def set_project(request, session, tool: str, project: str, analysis: str = None):
        """HTMX endpoint to update content based on project selection."""
        try:
            # Dynamically import based on tool name
            module = importlib.import_module(f"mq.tools.{tool}.report_web")
        except ImportError:
            return ft.Div(f"Unknown tool: {tool}", cls="error")

        if project:
            session["last_project"] = project

        return (
            *module.render_current(request, s_project_id=project, analysis=analysis),
            *module.render_history(request, s_project_id=project, analysis=analysis),
        )

    ################################################################################
    # Dynamic routes (ie. for each tool)
    ################################################################################
    for tool_name, tool_config in args.tools.items():
        # Create a closure to capture tool_name and tool_configuration
        def make_tool_route(name, config):
            @rt(f"/{name}")
            def render_tool_page_method(request, session):
                path_ = f"mq.tools.{name}.report_web"
                report_web: types.Module = importlib.import_module(path_)
                render_method = getattr(report_web, "render")
                return render_method(request, name, config, session)

            return render_tool_page_method

        make_tool_route(tool_name, tool_config)
