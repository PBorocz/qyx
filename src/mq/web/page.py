"""."""

from pathlib import Path

from fasthtml import common as ft

# from mq.web import render_project_selector

CSS = None  # Will be read ONCE on first render..


def render_navbar(request, active_page):
    """Render our navbar."""
    # Left nav is simply branding and link back to home page...
    kwargs = dict(aria_current="page") if not active_page else dict()
    l_nav = [ft.Li(ft.A("MQ", href="/", **kwargs))]

    for tool_name in sorted(request.app.state.args.tools.keys()):
        name = tool_name.title()
        path = f"/{tool_name}"
        kwargs = dict(aria_current="page") if active_page == tool_name else dict()
        l_nav.append(ft.Li(ft.A(name, href=path, **kwargs)))

    # Right nav is a listing of all the tools currently available.
    # r_nav = [*render_project_selector(request, "/partials")]
    # r_nav = []

    return ft.Nav(ft.Ul(*(l_nav)))


def render_page(request, title, active_page, *main_page_content):
    """Render the content provided into this base page template."""
    global CSS
    if not CSS:
        CSS = Path("src/mq/web/app.css").read_text(encoding="utf-8")

    s_title = "MQ"
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
            ft.Script(src="https://kozea.github.io/pygal.js/2.0.x/pygal-tooltips.min.js"),
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
