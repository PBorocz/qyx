"""Report data obo running 'cloc' tool."""

from datetime import datetime

from pygal import DateTimeLine
from pygal.style import CleanStyle
from fasthtml import common as fh

from mq.tools.base import Project, Scan

from mq.tools.cloc.models import query
from mq.web.routes.home import page


def render(request, name, config):
    """..."""
    return page(
        request,
        name,
        name.title(),
        *render_summary(request),
        *render_history(request),
    )


def _th_r(value: str) -> fh.Th:
    return fh.Th(value, scope="col", style="text-align: right")


def _th(value: str) -> fh.Th:
    return fh.Th(value, scope="col")


def _td_r(value: str) -> fh.Th:
    return fh.Td(value, style="text-align: right")


def _td(value: str) -> fh.Th:
    return fh.Td(value)


def render_summary(request):
    args = request.app.state.args
    project = Project.select().first()
    scan = Scan.get_most_recent(project, "cloc", "cloc")
    results = query(args, "0", scan=scan)

    return fh.Div(
        fh.H3("Current Status"),
        fh.H4(f"As Of {scan.as_of_display(full=False)}"),
        fh.Table(
            fh.Thead(
                fh.Tr(
                    _th_r("Code"),
                    _th_r("Comments"),
                    _th_r("Blanks"),
                    _th_r("TOTAL"),
                ),
            ),
            fh.Tbody(
                fh.Tr(
                    _td_r(f"{results.lines_code:,d}"),
                    _td_r(f"{results.lines_comment:,d}"),
                    _td_r(f"{results.lines_blank:,d}"),
                    _td_r(f"{results.lines_total:,d}"),
                ),
            ),
        ),
    )


def render_history(request):
    # Create Pygal chart
    args = request.app.state.args
    project = Project.select().first()
    args.options.last = 999
    timestamps, rows, _, _, _, _ = query(args, "history", project=project)
    # timestamps_formatted = format_timestamp_headers(timestamps)

    chart = DateTimeLine(
        x_title="Date",
        y_title="Lines",
        height=500,
        dots_size=2,
        x_label_rotation=45,  # Angle labels to prevent overlap
        x_labels_major_every=2,  # Show every 5th label
        tooltip_border_radius=10,
        x_value_formatter=lambda dt: dt.strftime("%Y-%m-%d %H:%M"),
        style=CleanStyle,
        # width=1200,
        # explicit_size=True,
    )
    datetime_values_cd = [(datetime.fromisoformat(row.timestamp), row.total_code) for row in rows]
    datetime_values_cm = [(datetime.fromisoformat(row.timestamp), row.total_comment) for row in rows]
    datetime_values_bl = [(datetime.fromisoformat(row.timestamp), row.total_blank) for row in rows]

    chart.add("Lines of Code", datetime_values_cd)
    chart.add("Comment Lines", datetime_values_cm)
    chart.add("Blank Lines", datetime_values_bl)

    # Render as SVG
    svg_chart = chart.render()  # Returns bytes

    return fh.Div(
        fh.H3("History"),
        fh.Div(fh.NotStr(svg_chart.decode("utf-8"))),
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
