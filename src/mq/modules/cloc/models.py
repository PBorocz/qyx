"""..."""

from argparse import Namespace
from decimal import Decimal
from datetime import datetime
from collections import defaultdict
from typing import Any
import logging

from peewee import fn, IntegerField

from mq.modules.base import BaseModuleModel, Project, Request, Scan
from mq.utils import rate_of_change_percentage

log = logging.getLogger(__name__)


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
        indexes = ((("scan", "dir", "filename"), True),)


def query(
    args: Namespace,
    level: str = "summary",
    project: Project = None,
    request: Request = None,
    scan: Scan = None,
) -> Any:
    match level.lower():
        case "0":
            return _query_summary(scan, percentages=args.options.percentages)
        case "1":
            return _query_detail(scan, percentages=args.options.percentages)
        case "2":
            return _query_full(scan, percentages=args.options.percentages)
        case "h" | "history":
            return _query_history(project, request, last=args.options.last)


def _query_summary(scan: Scan, percentages: bool = False) -> Any:
    row = (
        Cloc.select(
            fn.SUM(Cloc.lines_blank).alias("lines_blank"),
            fn.SUM(Cloc.lines_code).alias("lines_code"),
            fn.SUM(Cloc.lines_comment).alias("lines_comment"),
            (fn.SUM(Cloc.lines_blank) + fn.SUM(Cloc.lines_code) + fn.SUM(Cloc.lines_comment)).alias(
                "lines_total",
            ),
        )
        .where(Cloc.scan == scan)
        .get()
    )
    if percentages:
        # Convert to percentage of total:
        row.lines_blank = (row.lines_blank / row.lines_total) * 100.0
        row.lines_code = (row.lines_code / row.lines_total) * 100.0
        row.lines_comment = (row.lines_comment / row.lines_total) * 100.0
        row.lines_total = Decimal(100.0)
    return row


def _query_detail(scan: Scan, percentages: bool = False) -> Any:
    grand_total = _query_summary(scan, percentages=False)
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
        .where(Cloc.scan == scan)
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


def _query_full(scan: Scan, percentages: bool = False) -> [list[Cloc], dict[str, int], int]:
    rows = Cloc.select().where(Cloc.scan == scan).order_by(Cloc.dir, Cloc.filename)
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


def _query_history(project: Project, request: Request, last: int) -> tuple[list[str], defaultdict, defaultdict]:
    # TODO: Add support for percentages here..

    # If the most recent request (provided) has more than one scan,
    # use only the scan in THAT request! otherwise, scan over all the
    # scans for the project.
    if Scan.filter(Scan.request == request).count() > 1:
        # Essentially "git" mode, where our request triggered MULTIPLE scans (over time)
        scans = (
            Scan.select().where(Scan.request == request, Scan.module == MODULE).order_by(Scan.as_of.desc()).limit(last)
        )
    else:
        # Simple mode, our most recent request triggered on a single scan, consider all scans for the project:
        scans = (
            Scan.select()
            .join(Request)
            .where(
                Request.project == project,
                Scan.module == MODULE,
            )
            .order_by(Scan.as_of.desc())
            .limit(last)
        )

    query = (
        Cloc.select(
            Scan.as_of.alias("timestamp"),
            fn.SUM(Cloc.lines_code).alias("total_code"),
            fn.SUM(Cloc.lines_comment).alias("total_comment"),
            fn.SUM(Cloc.lines_blank).alias("total_blank"),
        )
        .join(Scan)
        .where(
            Scan.id.in_(scans),
        )
        .group_by(Scan.as_of)
        .order_by(Scan.as_of)
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

    roc = dict()
    for attr in ("Code", "Comment", "Blank"):
        if len(timestamps) > 1:
            roc[attr] = rate_of_change_percentage(
                transposed[attr][timestamps[-2]],
                transposed[attr][timestamps[-1]],
            )
        else:
            roc[attr] = 0.00
    if len(timestamps) > 1:
        roc["grand_total"] = rate_of_change_percentage(
            grand_totals[timestamps[-2]],
            grand_totals[timestamps[-1]],
        )
    else:
        roc["grand_total"] = 0.00

    adgs = dict()
    if len(timestamps) > 1:
        days = days_between(timestamps[0], timestamps[-1])
        # fmt: off
        adgs["total_code"   ] = (query[-1].total_code    - query[0].total_code   ) / days
        adgs["total_comment"] = (query[-1].total_comment - query[0].total_comment) / days
        adgs["total_blank"  ] = (query[-1].total_blank   - query[0].total_blank  ) / days
        # fmt: on
    return timestamps, query, transposed, grand_totals, roc, adgs


def days_between(timestamp1: str, timestamp2: str) -> float:
    """Calculate the number of days between two timestamp strings.

    Args:
        timestamp1: Earlier timestamp string (e.g., "2025-12-20 23:53:56+00:00")
        timestamp2: Later timestamp string (e.g., "2025-12-24 01:05:12+00:00")

    Returns:
        Number of days as a float (e.g., 3.05)
    """
    dt1 = datetime.fromisoformat(timestamp1)
    dt2 = datetime.fromisoformat(timestamp2)

    delta = dt2 - dt1
    return delta.total_seconds() / (24 * 60 * 60)
