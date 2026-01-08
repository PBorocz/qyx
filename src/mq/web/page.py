"""."""

from pathlib import Path

from fasthtml import common as ft

CSS = None  # Will be read ONCE on first render..


def render_navbar(request, active_page):
    """Render our navbar."""
    # Left nav is simply branding and link back to home page...
    l_nav = [ft.A("MQ", href="/")]

    # Right nav is a listing of all the tools currently available.
    r_nav = []
    for tool_name in sorted(request.app.state.args.tools.keys()):
        name = tool_name.title()
        path = f"/{tool_name}"
        kwargs = dict(aria_current="page") if active_page == name else dict()
        r_nav.append(ft.A(name, href=path, **kwargs))

    return ft.Nav(
        ft.Ul(*[ft.Li(a__) for a__ in l_nav]),
        ft.Ul(*[ft.Li(a__) for a__ in r_nav]),
    )


def render_page(request, title, active_page, *main_page_content):
    """Render the content provided into this base page template."""
    global CSS
    if not CSS:
        CSS = Path("src/mq/web/app.css").read_text(encoding="utf-8")

    return ft.Html(
        ft.Head(
            ft.Meta(charset="utf-8"),
            ft.Meta(name="viewport", content="width=device-width, initial-scale=1"),
            ft.Meta(name="color-scheme", content="light dark"),
            ft.Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css"),
            ft.Script(src="https://kozea.github.io/pygal.js/2.0.x/pygal-tooltips.min.js"),
            ft.Script(src="https://unpkg.com/htmx.org@1.9.10"),
            ft.Script(src="https://unpkg.com/tablesort@5.3.0/dist/tablesort.min.js"),
            ft.Script(src="https://unpkg.com/tablesort@5.3.0/dist/sorts/tablesort.number.min.js"),
            ft.Style(CSS),
            ft.Title(f"MQ-{title}"),
            lang="en",
        ),
        ft.Body(
            render_navbar(request, active_page),
            ft.Main(*main_page_content),
            cls="container-fluid",
        ),
        # ft.Footer(),
    )
