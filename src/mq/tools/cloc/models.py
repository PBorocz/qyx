"""..."""

from argparse import Namespace
from datetime import datetime
from collections import defaultdict
from typing import Any
import logging

from peewee import fn, IntegerField

from mq.tools.base import BaseResultsModel, Project, Request, Scan
from mq.utils import rate_of_change_percentage

log = logging.getLogger(__name__)


class Cloc(BaseResultsModel):
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
        indexes = ((("scan", "directory", "filename"), True),)


def query(level: str = "0", project: Project = None, scan: Scan = None, last: int = None) -> Any:
    match level.lower():
        case "0":
            return _query_0(scan)
        case "1":
            return _query_1(scan)
        case "2":
            return _query_2(scan)
        case "d":
            return _query_d(scan)
        case "h":
            return _query_h(project, last)


def _query_0(scan: Scan) -> Any:
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

    # Convert to percentage of total:
    row.lines_blank_p = (row.lines_blank / row.lines_total) * 100.0
    row.lines_code_p = (row.lines_code / row.lines_total) * 100.0
    row.lines_comment_p = (row.lines_comment / row.lines_total) * 100.0

    return row


def _query_1(scan: Scan) -> Any:
    grand_total = _query_0(scan)
    rows = (
        Cloc.select(
            Cloc.directory,
            fn.SUM(Cloc.lines_blank).alias("lines_blank"),
            fn.SUM(Cloc.lines_code).alias("lines_code"),
            fn.SUM(Cloc.lines_comment).alias("lines_comment"),
            (fn.SUM(Cloc.lines_blank) + fn.SUM(Cloc.lines_code) + fn.SUM(Cloc.lines_comment)).alias(
                "lines_total",
            ),
        )
        .where(Cloc.scan == scan)
        .group_by(Cloc.directory)
        .order_by(Cloc.directory)
    )
    # Convert to percentage of total:
    for row in rows:
        row.lines_code_p = (row.lines_code / grand_total.lines_code) * 100.0
        row.lines_blank_p = (row.lines_blank / grand_total.lines_blank) * 100.0
        row.lines_comment_p = (row.lines_comment / grand_total.lines_comment) * 100.0
        row.lines_total_p = (row.lines_total / grand_total.lines_total) * 100.0
    return rows


def _query_2(scan: Scan) -> [list[Cloc], dict[str, int], int]:
    rows = Cloc.select().where(Cloc.scan == scan).order_by(Cloc.directory, Cloc.filename)
    column_totals = defaultdict(int)
    for row in rows:
        column_totals["lines_blank"] += row.lines_blank
        column_totals["lines_comment"] += row.lines_comment
        column_totals["lines_code"] += row.lines_code
        row.lines_total = row.lines_blank + row.lines_comment + row.lines_code
    grand_total = sum(list(column_totals.values()))

    for row in rows:
        row.lines_code_p = (row.lines_code / column_totals["lines_code"]) * 100.0
        row.lines_comment_p = (row.lines_comment / column_totals["lines_blank"]) * 100.0
        row.lines_blank_p = (row.lines_blank / column_totals["lines_code"]) * 100.0
        row.lines_total_p = (row.lines_total / grand_total) * 100.0

    return rows, dict(column_totals), grand_total


def _query_h(project: Project, last: int = None) -> tuple[list[str], defaultdict, defaultdict]:
    # If the most recent request (provided) has more than one scan,
    # use only the scan in THAT request! otherwise, scan over all the
    # scans for the project.
    # if Scan.filter(Scan.request == request).count() > 1:
    #     # Essentially "git" mode, where our request triggered MULTIPLE scans (over time)
    #     scans = (
    #         Scan.select().where(Scan.request == request, Scan.tool == "cloc").order_by(Scan.as_of.desc()).limit(last)
    #     )
    # else:
    # Simple mode, our most recent request triggered on a single scan, consider all scans for the project:
    scans = (
        Scan.select()
        .join(Request)
        .where(
            Request.project == project,
            Scan.tool == "cloc",
        )
        .order_by(Scan.as_of.desc())
    )
    if last:
        scans = scans.limit(last)

    query = (
        Cloc.select(
            Scan.as_of.alias("timestamp"),
            fn.SUM(Cloc.lines_code).alias("total_code"),
            fn.SUM(Cloc.lines_comment).alias("total_comment"),
            fn.SUM(Cloc.lines_blank).alias("total_blank"),
        )
        .join(Scan)
        .where(Scan.id.in_(scans))
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


def _query_d(scan: Scan) -> Any:
    """Calculate all 'derived' report values."""
    row = _query_0(scan)

    ################################################################################
    # Calculate the "Code Density"
    ################################################################################
    code_density = (row.lines_code / (row.lines_code + row.lines_blank)) * 100.0
    if code_density >= 85.0:
        grade, color = "C", "#eab308"
    elif code_density >= 60.0:
        grade, color = "A", "#22c55e"
    elif code_density >= 10.0:
        grade, color = "B", "#84cc16"
    row.code_density = Namespace(score=code_density, grade=grade, color=color)

    ################################################################################
    # Calculate the "Comment Ratio"
    ################################################################################
    comment_ratio = row.lines_comment / (row.lines_code + row.lines_comment) * 100.0
    if comment_ratio >= 20.0:
        grade, color = "A", "#22c55e"
    elif comment_ratio >= 15.0:
        grade, color = "B", "#84cc16"
    elif comment_ratio >= 10.0:
        grade, color = "C", "#eab308"
    elif comment_ratio >= 5.0:
        grade, color = "D", "#f97316"
    else:
        grade, color = "F", "#ef4444"
    row.comment_ratio = Namespace(score=comment_ratio, grade=grade, color=color)

    return row


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
