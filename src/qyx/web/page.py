"""."""

from pathlib import Path

from fasthtml import common as ft


def render_navbar(request, active_page):
    """Render our navbar."""
    # Left nav:
    kwargs = dict(aria_current="page") if not active_page else dict()
    l_nav = [ft.Li(ft.A("QYX", href="/", **kwargs))]

    args = request.app.state.args
    for tool_name in args.config.get("renderers.web.ui.tool_order"):
        o_tool = args.tools.get(tool_name)
        if not o_tool.render_web_method:
            continue
        name = tool_name.title()
        path = f"/{tool_name}"
        kwargs = dict(aria_current="page") if active_page == tool_name else dict()
        l_nav.append(ft.Li(ft.A(name, href=path, **kwargs)))

    # Right nav:
    # r_nav = [*render_project_selector(request, "/partials")]
    # r_nav = []

    return ft.Nav(ft.Ul(*(l_nav)))


CSS = None  # Will be read ONCE on first render..


def render_page(request, title, active_page, *main_page_content):
    """Render the content provided into this base page template."""
    global CSS
    if not CSS:
        CSS = Path("src/qyx/web/static/css/app.css").read_text(encoding="utf-8")

    s_title = "QYX"
    if title:
        s_title += f"-{title}"

    return ft.Html(
        ft.Head(
            ft.Meta(charset="utf-8"),
            ft.Meta(name="viewport", content="width=device-width, initial-scale=1"),
            ft.Meta(name="color-scheme", content="light dark"),
            ft.Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css"),
            ft.Link(rel="apple-touch-icon", sizes="180x180", href="/apple-touch-icon.png"),
            ft.Link(rel="icon", type="image/png", sizes="32x32", href="/favicon-32x32.png"),
            ft.Link(rel="icon", type="image/png", sizes="16x16", href="/favicon-16x16.png"),
            ft.Link(rel="manifest", href="/site.webmanifest"),
            ft.Script(src="https://unpkg.com/htmx.org@1.9.10"),
            ft.Script(src="https://unpkg.com/tablesort@5.3.0/dist/tablesort.min.js"),
            ft.Script(src="https://unpkg.com/tablesort@5.3.0/dist/sorts/tablesort.number.min.js"),
            ft.Style(CSS),
            ft.Title(s_title),
            lang="en",
        ),
        ft.Body(
            render_navbar(request, active_page),
            ft.Main(*main_page_content),
            cls="container-fluid",
        ),
        # ft.Footer(),
    )
