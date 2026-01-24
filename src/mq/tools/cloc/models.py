"""..."""

import logging
from argparse import Namespace
from collections import defaultdict
from datetime import datetime
from typing import Any

from peewee import IntegerField, fn

from mq.tools.base import BaseResultsModel, Project, Request, Scan
from mq.utils import bucket, rate_of_change_percentage
from mq.utils.scoring import get_nested_config, score_metric


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


def query(args: Namespace, level: str = "0", project: Project = None, scan: Scan = None, last: int = None) -> Any:
    match level.lower():
        case "0":
            return _query_0(scan)
        case "1":
            return _query_1(scan)
        case "2":
            return _query_2(scan)
        case "d":
            return _query_d(args, scan)
        case "f":
            return _query_f(args, scan)
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

    # Find the number of files
    row.files_total = Cloc.select(fn.COUNT(Cloc.id).alias("files_total")).where(Cloc.scan == scan).get().files_total

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


def _query_d(args: Namespace, scan: Scan) -> Any:
    """Calculate all 'derived' report values."""
    row = _query_0(scan)

    # Calculate the "Code Density"
    metric_value = (row.lines_code / (row.lines_code + row.lines_blank)) * 100.0
    row.code_density = score_metric(args, "tools.cloc.code_density", metric_value)

    # Calculate the "Comment Ratio"
    metric_value = row.lines_comment / (row.lines_code + row.lines_comment) * 100.0
    row.comment_ratio = score_metric(args, "tools.cloc.comment_ratio", metric_value)

    # Calculate average lines per file
    metric_value = int(row.lines_code / row.files_total)
    row.avg_lines_per_file = score_metric(args, "tools.cloc.avg_lines_per_file", metric_value)

    return row


def _query_f(args: Namespace, scan: Scan) -> list[tuple[str, int]]:
    """Calculate histogram buckets over filesize."""
    buckets = get_nested_config(args.config, "tools.cloc.histogram_file_size.buckets")
    bucket_breaks = [level["min"] for level in buckets]

    # Calculate file density histogram
    file_sizes = [
        row.lines_code + row.lines_comment + row.lines_blank for row in Cloc.select().where(Cloc.scan == scan)
    ]
    histogram_by_file_size = bucket(file_sizes, bucket_breaks, as_percentage=True)

    return histogram_by_file_size


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
