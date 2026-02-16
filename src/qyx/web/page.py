"""Core page rendering methods, full (Bottle) and partial (HTMX)."""

from bottle import request


def render_page(title: str, template: str, **context) -> str:
    """Render the specified page template using the context provided."""
    context["title"] = title
    context["navbar"] = [
        {"name": tool_name, "description": tool_name.title()}
        for tool_name in request.app.args.config.get("renderers.web.ui.tool_order")
    ]
    template = request.app.args.jinja_env.get_template(template)
    return template.render(**context)


def render_partial(template: str, **context) -> str:
    """Render the specified page template using the context provided."""
    return request.app.args.jinja_env.get_template(template).render(**context)
