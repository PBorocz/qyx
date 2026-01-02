"""Report data obo running 'cloc' tool."""

from datetime import datetime

from pygal import DateTimeLine
from pygal.style import Style
from fasthtml import common as fh

from mq.tools.base import Project, Scan

from mq.tools.cloc.models import query
from mq.web.page import render_page


def render(request, name, config):
    """..."""
    return render_page(
        request,
        name,
        name.title(),
        *render_project_selector(request),
        fh.Div(
            *render_current_status(request, None),
            *render_history(request, None),
            id="project-content",  # Target for out HTMX updates!
        ),
    )


################################################################################################
# Project Selector
################################################################################################
def render_project_selector(request):
    fh_select_items = [fh.Option("Project...", value="")]
    for project in Project.select().order_by(Project.name):
        fh_select_items.append(fh.Option(project.name, value=str(project.id)))

    return fh.Form(
        fh.Fieldset(
            fh.Select(
                *fh_select_items,
                name="project",
                aria_label="Select your project...",
                hx_get="/cloc_update-project",  # HTMX endpoint
                hx_target="#project-content",  # Where to update
                hx_swap="innerHTML",  # How to update
                hx_trigger="change",  # Trigger on selection change
            ),
        ),
    )


################################################################################################
# Current Status..
################################################################################################
def render_current_status(request, s_project: str = None):
    if not s_project:
        return fh.Section()
    args = request.app.state.args
    project = Project.get(Project.id == int(s_project))
    scan = Scan.get_most_recent(project, "cloc", "cloc")
    results = query(args, "0", scan=scan)

    return fh.Section(
        fh.H1("Current Status"),
        fh.H4(f"As Of {scan.as_of_display(full=False)}"),
        fh.Div(
            fh.Table(
                fh.Thead(
                    fh.Tr(
                        fh.Th("Lines of Code", scope="col", style="text-align: right"),
                        fh.Th("Comment Lines", scope="col", style="text-align: right"),
                        fh.Th("Blank Lines", scope="col", style="text-align: right"),
                        fh.Th("TOTAL", scope="col", style="text-align: right"),
                    ),
                ),
                fh.Tbody(
                    fh.Tr(
                        fh.Td(f"{results.lines_code:,d}", style="text-align: right"),
                        fh.Td(f"{results.lines_comment:,d}", style="text-align: right"),
                        fh.Td(f"{results.lines_blank:,d}", style="text-align: right"),
                        fh.Td(f"{results.lines_total:,d}", style="text-align: right"),
                    ),
                ),
            ),
            cls="div",
        ),
    )


################################################################################################
# History
################################################################################################
def render_history(request, s_project: str = None):
    # Create Pygal chart
    if not s_project:
        return fh.Section()
    project = Project.get(Project.id == int(s_project))
    args = request.app.state.args
    args.options.last = 999  # Override to get ALL the data we have!
    timestamps, rows, _, _, _, _ = query(args, "history", project=project)

    custom_style = Style(
        background="transparent",
        font_family="Inter",
        guide_stroke_color="#cccccc",  # Lighter minor lines
        guide_stroke_dasharray="2,4",  # Different dash for minor
        guide_stroke_width=0.5,  # Thinner minor lines
        major_guide_stroke_color="#333333",  # Darker major lines
        major_guide_stroke_dasharray="6,6",  # Dashed major lines
        major_guide_stroke_width=2,  # Thicker major lines
        transition="400ms ease-in",
    )

    chart = DateTimeLine(
        y_title="Lines",
        dots_size=1,
        height=500,
        legend_at_bottom=True,
        legend_at_bottom_columns=3,
        style=custom_style,
        tooltip_border_radius=10,
        x_label_rotation=45,  # Angle labels to prevent overlap
        x_labels_major_every=2,  # Show every 5th label
        x_value_formatter=lambda dt: dt.strftime("%Y-%m-%d %H:%M"),
    )
    datetime_values_cd = [(datetime.fromisoformat(row.timestamp), row.total_code) for row in rows]
    datetime_values_cm = [(datetime.fromisoformat(row.timestamp), row.total_comment) for row in rows]
    datetime_values_bl = [(datetime.fromisoformat(row.timestamp), row.total_blank) for row in rows]

    chart.add("Code", datetime_values_cd)
    chart.add("Comments", datetime_values_cm)
    chart.add("Blanks", datetime_values_bl)

    # Render as SVG
    svg_chart = chart.render()  # Returns bytes

    return fh.Section(
        fh.H1("History", style="margin-top: 1rem;"),
        fh.Div(
            fh.NotStr(svg_chart.decode("utf-8")),
            cls="div",
        ),
    )


# def render_history(request):
#     # Create Pygal chart
#     args = request.app.state.args
#     project = Project.select().first()
#     args.options.last = 999
#     timestamps, rows, _, _, _, _ = query(args, "history", project=project)
#     timestamps_formatted = format_timestamp_headers(timestamps)

#     chart = pygal.Line(
#         # title="History",
#         x_title="Date",
#         y_title="Lines",
#         width=1200,
#         height=500,
#         explicit_size=True,
#         dots_size=2,
#         x_label_rotation=45,  # Angle labels to prevent overlap
#         show_minor_x_labels=False,  # Only show some labels
#         x_labels_major_every=5,  # Show every 5th label
#         tooltip_border_radius=10,
#         formatter=lambda x: f"{x:,.0f}",  # Format numbers in tooltip
#     )
#     chart.x_labels = [timestamps_formatted[row.timestamp] for row in rows]
#     chart.add("Code", [row.total_code for row in rows])
#     chart.add("Comment", [row.total_comment for row in rows])
#     chart.add("Blank", [row.total_blank for row in rows])  # Just values

#     # Render as SVG
#     svg_chart = chart.render()  # Returns bytes

#     return fh.Div(
#         fh.H3("History", cls="text-3xl font-bold mb-2"),
#         fh.Div(
#             fh.NotStr(svg_chart.decode("utf-8")),  # Raw SVG HTML
#         ),
#     )


# def render_history(request):
#     args = request.app.state.args
#     project = Project.select().first()
#     args.options.last = 999
#     timestamps, rows, _, _, _, _ = query(args, "history", project=project)
#     timestamps_formatted = format_timestamp_headers(timestamps)

#     tr_s = []
#     for row in rows:
#         tr_ = fh.Tr(
#             _td(timestamps_formatted[row.timestamp]),
#             _td_r(f"{row.total_code:,d}"),
#             _td_r(f"{row.total_comment:,d}"),
#             _td_r(f"{row.total_blank:,d}"),
#         )
#         tr_s.append(tr_)

#     return fh.Div(
#         fh.H3("History"),
#         fh.Table(
#             fh.Thead(
#                 fh.Tr(
#                     _th("As Of"),
#                     _th_r("Code"),
#                     _th_r("Comments"),
#                     _th_r("Blanks"),
#                 ),
#             ),
#             fh.Tbody(*tr_s),
#             cls="striped",
#         ),
#     )


# def render_detail(run: Run) -> Any:
#     column_total = query_summary(run)
#     detail_rows = query_detail(run)

#     th_s = [
#         _th("Directory"),
#         _th_r("Code"),
#         _th_r("Comments"),
#         _th_r("Blanks"),
#         _th_r("TOTAL"),
#     ]

#     tr_s = []  # Table rows...
#     for result in detail_rows:
#         td_s = [  # TD elements...
#             _td(result.dir),
#             _td_r(result.lines_code),
#             _td_r(result.lines_blank),
#             _td_r(result.lines_comment),
#             _td_r(result.lines_total),
#         ]
#         tr_s.append(fh.Tr(*td_s))

#     tfoot_s = [
#         _th("TOTAL"),
#         _td_r(column_total.lines_code),
#         _td_r(column_total.lines_blank),
#         _td_r(column_total.lines_comment),
#         _td_r(column_total.lines_total),
#     ]

#     return fh.Div(
#         fh.Hr(),
#         fh.H4("CLOC Detail"),
#         fh.Table(
#             fh.Thead(fh.Tr(*th_s)),
#             fh.Tbody(*tr_s),
#             fh.Tfoot(fh.Tr(*tfoot_s)),
#         ),
#     )


# def render_full(run: Run) -> Any:
#     rows, column_totals, grand_total = query_full(run)

#     th_s = [
#         _th("Directory"),
#         _th_r("Code"),
#         _th_r("Comments"),
#         _th_r("Blanks"),
#         _th_r("TOTAL"),
#     ]

#     tr_s = []  # Table rows...
#     for row in rows:
#         td_s = [  # TD elements...
#             _td(f"{row.dir}/{row.filename}"),
#             _td_r(row.lines_code),
#             _td_r(row.lines_blank),
#             _td_r(row.lines_comment),
#             _td_r(row.lines_total),
#         ]
#         tr_s.append(fh.Tr(*td_s))

#     tfoot_s = [
#         _th("TOTAL"),
#         _td_r(column_totals["lines_code"]),
#         _td_r(column_totals["lines_blank"]),
#         _td_r(column_totals["lines_comment"]),
#         _td_r(grand_total),
#     ]

#     return fh.Div(
#         fh.Hr(),
#         fh.H4("CLOC Full"),
#         fh.Table(
#             fh.Thead(fh.Tr(*th_s)),
#             fh.Tbody(*tr_s),
#             fh.Tfoot(fh.Tr(*tfoot_s)),
#         ),
#     )


# def render_history(project: Project) -> Any:
#     timestamps, transposed, grand_totals = query_history(project)
#     timestamps_formatted = format_timestamp_headers(timestamps)
#     th_s = [_th("Metric")]
#     for timestamp in sorted(timestamps):
#         th_s.append(_th_r(timestamps_formatted[timestamp]))

#     tr_s = []
#     for metric, dt_rows in transposed.items():
#         td_s = [_th(metric)]
#         for timestamp in sorted(timestamps):
#             td_s.append(_td_r(str(dt_rows[timestamp])))
#         tr_s.append(fh.Tr(*td_s))

#     tfoot_s = [_th("TOTAL")]
#     for timestamp in sorted(timestamps):
#         tfoot_s.append(_td_r(str(grand_totals[timestamp])))

#     return fh.Div(
#         fh.Hr(),
#         fh.H4("CLOC Results Over Time"),
#         fh.Table(
#             fh.Thead(fh.Tr(*th_s)),
#             fh.Tbody(*tr_s),
#             fh.Tfoot(fh.Tr(*tfoot_s)),
#             cls="striped",
#         ),
#     )
