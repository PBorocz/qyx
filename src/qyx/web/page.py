"""Core page rendering methods, full (Bottle) and partial (HTMX)."""

from bottle import request


def render_page(title: str, template: str, **context) -> str:
    """Render the specified *FULL* page template using the context provided."""
    context["title"] = title
    context["navbar"] = [
        {"name": tool_name, "description": tool_name.title()}
        for tool_name in request.app.args.config.get("renderers.web.ui.tool_order")
    ]
    return _render_template(template, **context)


def render_partial(template: str, **context) -> str:
    """Render the specified *PARTIAL* page template (usually a .htmx one) using the context provided."""
    return _render_template(template, **context)


def _render_template(template: str, **context) -> str:
    """Lowest level, render the template provided using the context provided."""
    context["current_path"] = request.path  # Pass back for Navbar management.
    return request.app.args.jinja_env.get_template(template).render(**context)
