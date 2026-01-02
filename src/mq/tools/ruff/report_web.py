"""Report data obo running 'cloc' tool."""

# from typing import Any

# from fasthtml import ft
from fasthtml import common as fh

# from mq.tools.base import Project, Run
# from mq.tools.cloc.models import query_detail, query_full, query_history, query_summary
# from mq.utils import format_timestamp_headers
from mq.web.page import render_page


def render(request, name, config):
    """..."""
    return render_page(
        request,
        name.title(),
        name.title(),
        fh.H1("Most Recent Analysis", cls="text-3xl font-bold mb-4"),
        fh.P(f"Configuration: {config}", cls="text-gray-600"),
    )


# def _th_r(value: str) -> ft.Th:
#     return ft.Th(value, scope="col", style="font-family: monospace; text-align: right;")


# def _th(value: str) -> ft.Th:
#     return ft.Th(value, scope="col", style="font-family: monospace")


# def _td_r(value: str) -> ft.Th:
#     return ft.Td(value, scope="row", style="font-family: monospace; text-align: right;")


# def _td(value: str) -> ft.Th:
#     return ft.Td(value, scope="row", style="font-family: monospace")


# def render_summary(run: Run) -> Any:
#     results = query_summary(run)

#     return ft.Div(
#         ft.Hr(),
#         ft.H4("CLOC Summary"),
#         ft.Table(
#             ft.Thead(
#                 ft.Tr(
#                     _th_r("Code"),
#                     _th_r("Comments"),
#                     _th_r("Blanks"),
#                     _th_r("TOTAL"),
#                 ),
#             ),
#             ft.Tbody(
#                 ft.Tr(
#                     _td_r(f"{results.lines_code}"),
#                     _td_r(f"{results.lines_comment}"),
#                     _td_r(f"{results.lines_blank}"),
#                     _td_r(f"{results.lines_total}"),
#                 ),
#             ),
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
#         tr_s.append(ft.Tr(*td_s))

#     tfoot_s = [
#         _th("TOTAL"),
#         _td_r(column_total.lines_code),
#         _td_r(column_total.lines_blank),
#         _td_r(column_total.lines_comment),
#         _td_r(column_total.lines_total),
#     ]

#     return ft.Div(
#         ft.Hr(),
#         ft.H4("CLOC Detail"),
#         ft.Table(
#             ft.Thead(ft.Tr(*th_s)),
#             ft.Tbody(*tr_s),
#             ft.Tfoot(ft.Tr(*tfoot_s)),
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
#         tr_s.append(ft.Tr(*td_s))

#     tfoot_s = [
#         _th("TOTAL"),
#         _td_r(column_totals["lines_code"]),
#         _td_r(column_totals["lines_blank"]),
#         _td_r(column_totals["lines_comment"]),
#         _td_r(grand_total),
#     ]

#     return ft.Div(
#         ft.Hr(),
#         ft.H4("CLOC Full"),
#         ft.Table(
#             ft.Thead(ft.Tr(*th_s)),
#             ft.Tbody(*tr_s),
#             ft.Tfoot(ft.Tr(*tfoot_s)),
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
#         tr_s.append(ft.Tr(*td_s))

#     tfoot_s = [_th("TOTAL")]
#     for timestamp in sorted(timestamps):
#         tfoot_s.append(_td_r(str(grand_totals[timestamp])))

#     return ft.Div(
#         ft.Hr(),
#         ft.H4("CLOC Results Over Time"),
#         ft.Table(
#             ft.Thead(ft.Tr(*th_s)),
#             ft.Tbody(*tr_s),
#             ft.Tfoot(ft.Tr(*tfoot_s)),
#             cls="striped",
#         ),
#     )
