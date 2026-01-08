"""."""

from fasthtml import common as ft


STYLE = """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

   :root {
      --pico-font-size: 80%;
      --pico-font-family: 'Inter', sans-serif;
      --pico-primary: #2563eb;
      --pico-primary-hover: #1d4ed8;
   }

   /* Get the accordian "arrow" to display right after the text instead of right-aligned. */
   details summary {
      max-width: fit-content;
   }

   /* Make "small"...well...small! */
   small {
      font-size: 0.75rem;
   }

   /* Make tables more compact */
   table {
      font-size: 0.9rem;
      width: auto;
   }
   table th, table td {
      padding: 0.2rem 0.5rem;
   }

   /* Style the navbar differently */
   nav {
       background-color: #f8f9fa;
       border-bottom: 2px solid #e9ecef;
   }

   /* Make charts responsive */
   svg {
       max-width: 100%;
       height: auto;
   }

   /* Custom heading spacing */
   h1 {
       # margin-bottom: 1rem;
   }

   h2 {
       margin-bottom: 0.75rem;
       color: #6c757d;
   }

   /* Our simple "section" container (ie. border) */
   .bordered {
       border: 1px solid #dee2e6;
       border-radius: 0.5rem;
       padding: 0rem;
       background: white;
    }

    th[role=columnheader]:not(.no-sort) {
        cursor: pointer;
    }
    th[role=columnheader]:not(.no-sort):after {
        content: '';
        float: right;
        margin-top: 0.2em;
        margin-left: 0.25em;
        font-size: 0.7em;
        visibility: hidden;
    }
    th[aria-sort=ascending]:not(.no-sort):after {
        content: '↑';
        visibility: visible;
    }
    th[aria-sort=descending]:not(.no-sort):after {
        content: '↓';
        visibility: visible;
    }

"""


def render_navbar(request, active_page):
    """Render our navbar."""
    # Left nav is simply branding and link back to home page...
    l_nav = [ft.A("MQ", href="/")]

    # Right nav is a listing of all the tools currently available.
    r_nav = []
    for tool_name, tool_config in request.app.state.args.tools.items():
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
            ft.Style(STYLE),
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
