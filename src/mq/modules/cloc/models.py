"""..."""

from argparse import Namespace
from decimal import Decimal
from collections import defaultdict
from typing import Any

from peewee import fn, IntegerField

from mq.modules.base import BaseModuleModel, Project, Run
from mq.modules.cloc import MODULE


class Cloc(BaseModuleModel):
    """..."""

    # fmt: off
    lines_blank   = IntegerField(null=True)
    lines_code    = IntegerField(null=True)
    lines_comment = IntegerField(null=True)
    scale_factor  = IntegerField(null=True)
    # fmt: on

    class Meta:
        """Define peewee meta data."""

        table_name = "cloc"
        indexes = ((("run", "dir", "filename"), True),)


def query(args: Namespace, level: str = "summary", run: Run = None, project: Project = None) -> Any:
    match level.lower():
        case "summary":
            return _query_summary(run, percentages=args.percentages)
        case "detail":
            return _query_detail(run, percentages=args.percentages)
        case "full":
            return _query_full(run, percentages=args.percentages)
        case "history":
            return _query_history(project)


def _query_summary(run: Run, percentages: bool = False) -> Any:
    row = (
        Cloc.select(
            fn.SUM(Cloc.lines_blank).alias("lines_blank"),
            fn.SUM(Cloc.lines_code).alias("lines_code"),
            fn.SUM(Cloc.lines_comment).alias("lines_comment"),
            (fn.SUM(Cloc.lines_blank) + fn.SUM(Cloc.lines_code) + fn.SUM(Cloc.lines_comment)).alias(
                "lines_total",
            ),
        )
        .where(Cloc.run == run.id)
        .get()
    )
    if percentages:
        # Convert to percentage of total:
        row.lines_blank = (row.lines_blank / row.lines_total) * 100.0
        row.lines_code = (row.lines_code / row.lines_total) * 100.0
        row.lines_comment = (row.lines_comment / row.lines_total) * 100.0
        row.lines_total = Decimal(100.0)
    return row


def _query_detail(run: Run, percentages: bool = False) -> Any:
    grand_total = _query_summary(run, percentages=False)
    rows = (
        Cloc.select(
            Cloc.dir,
            fn.SUM(Cloc.lines_blank).alias("lines_blank"),
            fn.SUM(Cloc.lines_code).alias("lines_code"),
            fn.SUM(Cloc.lines_comment).alias("lines_comment"),
            (fn.SUM(Cloc.lines_blank) + fn.SUM(Cloc.lines_code) + fn.SUM(Cloc.lines_comment)).alias(
                "lines_total",
            ),
        )
        .where(Cloc.run == run.id)
        .group_by(Cloc.dir)
        .order_by(Cloc.dir)
    )
    if percentages:
        # Convert to percentage of total:
        for row in rows:
            row.lines_code = (row.lines_code / grand_total.lines_code) * 100.0
            row.lines_blank = (row.lines_blank / grand_total.lines_blank) * 100.0
            row.lines_comment = (row.lines_comment / grand_total.lines_comment) * 100.0
            row.lines_total = (row.lines_total / grand_total.lines_total) * 100.0
    return rows


def _query_full(run: Run, percentages: bool = False) -> [list[Cloc], dict[str, int], int]:
    rows = Cloc.select().where(Cloc.run == run).order_by(Cloc.dir, Cloc.filename)
    column_totals = defaultdict(int)
    for row in rows:
        column_totals["lines_blank"] += row.lines_blank
        column_totals["lines_comment"] += row.lines_comment
        column_totals["lines_code"] += row.lines_code
        row.lines_total = row.lines_blank + row.lines_comment + row.lines_code
    grand_total = sum(list(column_totals.values()))

    if percentages:
        for row in rows:
            row.lines_code = (row.lines_code / column_totals["lines_code"]) * 100.0
            row.lines_comment = (row.lines_comment / column_totals["lines_blank"]) * 100.0
            row.lines_blank = (row.lines_blank / column_totals["lines_code"]) * 100.0
            row.lines_total = (row.lines_total / grand_total) * 100.0

        column_totals["lines_blank"] = (column_totals["lines_blank"] / grand_total) * 100.0
        column_totals["lines_code"] = (column_totals["lines_code"] / grand_total) * 100.0
        column_totals["lines_comment"] = (column_totals["lines_comment"] / grand_total) * 100.0
        grand_total = 100.0
    return rows, dict(column_totals), grand_total


def _query_history(project: Project) -> tuple[list[str], defaultdict, defaultdict]:
    # TODO: Add support for parsing args.options to pull out last:<d>
    # TODO: Add support for percentages here..
    args_last = 2
    runs = (
        Run.select()
        .where(
            Run.project == project,
            Run.module == MODULE,
        )
        .order_by(Run.timestamp.desc())
        .limit(args_last)
    )

    query = (
        Cloc.select(
            Run.timestamp.alias("timestamp"),
            fn.SUM(Cloc.lines_code).alias("total_code"),
            fn.SUM(Cloc.lines_comment).alias("total_comment"),
            fn.SUM(Cloc.lines_blank).alias("total_blank"),
        )
        .join(Run)
        .where(
            Run.id.in_(runs),
        )
        .group_by(Run.timestamp)
        .order_by(Run.timestamp)
        .objects()
    )

    ################################################################################################
    # Transpose (to get timestamps *across* instead of down and calculate grand totals)
    ################################################################################################
    timestamps = [result.timestamp for result in query]
    transposed = defaultdict(lambda: defaultdict(dict))
    grand_totals = defaultdict(int)
    for result in query:
        transposed["Code"][result.timestamp] = result.total_code
        transposed["Comment"][result.timestamp] = result.total_comment
        transposed["Blank"][result.timestamp] = result.total_blank

        # Calculate grand totals for each timestamp as we go
        grand_totals[result.timestamp] += result.total_code + result.total_comment + result.total_blank

    return timestamps, transposed, grand_totals
