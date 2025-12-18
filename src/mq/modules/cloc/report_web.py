"""Report data obo running 'cloc' tool."""

import logging
from typing import Any

from fasthtml import ft

from mq.modules.models import Project, Run
from mq.modules.cloc.models import query_history, query_summary
from mq.utilities import format_timestamp_headers

uvicorn_logger = logging.getLogger("uvicorn")


def render_summary(run: Run) -> Any:
    results = query_summary(run)

    return ft.Div(
        ft.Table(
            ft.Thead(
                ft.Tr(
                    ft.Th("Code", scope="col"),
                    ft.Th("Comments", scope="col"),
                    ft.Th("Blanks", scope="col"),
                    ft.Th("TOTAL", scope="col"),
                ),
            ),
            ft.Tbody(
                ft.Tr(
                    ft.Td(f"{results.lines_code}", scope="row"),
                    ft.Td(f"{results.lines_comment}"),
                    ft.Td(f"{results.lines_blank}"),
                    ft.Td(f"{results.lines_total}"),
                ),
            ),
        ),
    )


def render_history(project: Project) -> Any:
    timestamps, transposed, grand_totals = query_history(project)

    th_s = [ft.Th("Metric", scope="col")]
    for i, header in enumerate(format_timestamp_headers(timestamps)):
        th_s.append(ft.Th(header, scope="col", style="text-align: right;"))

    tr_s = []
    for metric, dt_rows in transposed.items():
        td_s = [ft.Th(metric, scope="row")]
        for timestamp in timestamps:
            td_s.append(ft.Td(str(dt_rows[timestamp]), style="text-align: right;"))
        tr_s.append(ft.Tr(*td_s))

    return ft.Div(
        ft.Hr(),
        ft.H3("CLOC Results Over Time"),
        ft.Table(ft.Thead(ft.Tr(*th_s)), ft.Tbody(*tr_s), cls="striped"),
    )
