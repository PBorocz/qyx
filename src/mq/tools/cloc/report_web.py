"""Report data obo running 'cloc' tool."""

# from typing import Any

from fasthtml import common as fh

from mq.tools.base import Project, Scan

from mq.tools.cloc.models import query
from mq.utils import format_timestamp_headers
from mq.web.routes.home import page


def render(request, name, config):
    """..."""
    return page(
        request,
        name.title(),
        name.title(),
        *render_summary(request),
        *render_history(request),
        # fh.H1("Most Recent Analysis", cls="text-3xl font-bold mb-4"),
        # fh.P(f"Configuration: {config}", cls="text-gray-600"),
    )


def _th_r(value: str) -> fh.Th:
    return fh.Th(value, cls="px-6 py-3 text-xs font-medium text-gray-700 uppercase tracking-wider text-right")


def _th(value: str) -> fh.Th:
    return fh.Th(value, cls="px-6 py-3 text-xs font-medium text-gray-700 uppercase tracking-wider")


def _td_r(value: str) -> fh.Th:
    return fh.Td(value, cls="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right ")


def _td(value: str) -> fh.Th:
    return fh.Td(value, cls="px-6 py-4 whitespace-nowrap text-sm text-gray-900")


def render_summary(request):
    args = request.app.state.args
    project = Project.select().first()
    scan = Scan.get_most_recent(project, "cloc", "cloc")
    results = query(args, "0", scan=scan)

    return fh.Div(
        # fh.Hr(),
        fh.H1("Summary", cls="text-3xl font-bold mb-2"),
        fh.H2(f"As Of {scan.as_of_display(full=False)}", cls="text-xl text-gray-600 mb-4"),
        fh.Table(
            fh.Thead(
                fh.Tr(
                    _th_r("Code"),
                    _th_r("Comments"),
                    _th_r("Blanks"),
                    _th_r("TOTAL"),
                    cls="border-b-2 border-gray-300",
                ),
                cls="bg-gray-50",
            ),
            fh.Tbody(
                fh.Tr(
                    _td_r(f"{results.lines_code:,d}"),
                    _td_r(f"{results.lines_comment:,d}"),
                    _td_r(f"{results.lines_blank:,d}"),
                    _td_r(f"{results.lines_total:,d}"),
                    cls="border-b border-gray-200",
                ),
            ),
            cls="min-w-full divide-y divide-gray-200",
        ),
        cls="overflow-hidden shadow ring-1 ring-black ring-opacity-5 rounded-lg",
    )


def render_history(request):
    args = request.app.state.args
    project = Project.select().first()
    timestamps, rows, transposed, grand_totals, roc, adgs = query(args, "history", project=project)
    timestamps_formatted = format_timestamp_headers(timestamps)

    tr_s = []
    for row in rows:
        tr_ = fh.Tr(
            _td(timestamps_formatted[row.timestamp]),
            _td_r(f"{row.total_code:,d}"),
            _td_r(f"{row.total_comment:,d}"),
            _td_r(f"{row.total_blank:,d}"),
            cls="border-b border-gray-200",
        )
        tr_s.append(tr_)

    return fh.Div(
        fh.Br(),
        fh.H1("History", cls="text-3xl font-bold mb-2"),
        fh.Table(
            fh.Thead(
                fh.Tr(
                    _th("As Of"),
                    _th_r("Code"),
                    _th_r("Comments"),
                    _th_r("Blanks"),
                    cls="border-b-2 border-gray-300",
                ),
                cls="bg-gray-50",
            ),
            fh.Tbody(*tr_s),
            cls="min-w-full divide-y divide-gray-200",
        ),
        cls="overflow-hidden shadow ring-1 ring-black ring-opacity-5 rounded-lg",
    )


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
