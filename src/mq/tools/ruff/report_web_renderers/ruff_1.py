"""Report data obo running 'ruff' tool for level 1."""

from argparse import Namespace

from fasthtml import common as fh

from mq.tools.base import Scan
from mq.tools.ruff.models import query
from mq.tools.ruff import get_ruff_rule_name


def ruff_1(args: Namespace, scan: Scan):
    summary = query(args, "0", scan=scan)
    results = query(args, "1", scan=scan)

    t_head = fh.Tr(
        fh.Th("Rule", scope="col", style="text-align: left"),
        fh.Th("Count", scope="col", style="text-align: right"),
        fh.Th("Message", scope="col", style="text-align: left"),
    )

    t_body = []
    for result in results:
        rule_name = get_ruff_rule_name(result.rule_code)
        t_row = fh.Tr(
            fh.Td(result.rule_code, style="text-align: left"),
            fh.Td(f"{result.count:,d}", style="text-align: right"),
            fh.Td(rule_name.title(), style="text-align: left"),
        )
        t_body.append(t_row)

    t_total = fh.Tr(
        fh.Td("TOTAL", style="text-align: left"),
        fh.Td(f"{summary.count:,d}", style="text-align: right"),
        fh.Td(""),
    )

    return (
        fh.Table(
            fh.Thead(t_head),
            fh.Tbody(*t_body),
            fh.Tfoot(t_total),
            id="level_1",
        ),
        fh.Script("new Tablesort(document.getElementById('level_1'));"),
    )
