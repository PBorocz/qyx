"""..."""

import logging
from argparse import Namespace
from collections import defaultdict
from datetime import datetime
from types import SimpleNamespace as Sns

import peewee as pw
from peewee import fn

from qyx.constants import ViewContext as Vc
from qyx.tools._models_ import BaseModel, Project, Scan
from qyx.tools.common import get_scans_for_project_dimension
from qyx.utils import bucket, rate_of_change_percentage
from qyx.utils.scoring import score_metric


log = logging.getLogger(__name__)


class Cloc(BaseModel):
    """Cloc tool line of code storage."""

    # fmt: off
    id            = pw.AutoField()
    scan          = pw.ForeignKeyField(Scan, on_delete="CASCADE")
    directory     = pw.CharField(help_text="eg. src/qyx/") # Relative to project's root!
    filename      = pw.CharField(help_text="eg. foo.py")
    lines_blank   = pw.IntegerField(null=True)
    lines_code    = pw.IntegerField(null=True)
    lines_comment = pw.IntegerField(null=True)
    scale_factor  = pw.IntegerField(null=True)

    # fmt: on

    class Meta:
        """Define peewee meta data."""

        table_name = "tool_cloc"
        indexes = ((("scan", "directory", "filename"), True),)


def query_cloc_0(args: Namespace, scan: Scan, dimension: str = "cloc", context: Vc = Vc.TOOL_HOME) -> Sns:
    query = (
        Cloc.select(
            fn.SUM(Cloc.lines_blank).alias("lines_blank"),
            fn.SUM(Cloc.lines_code).alias("lines_code"),
            fn.SUM(Cloc.lines_comment).alias("lines_comment"),
            (fn.SUM(Cloc.lines_blank) + fn.SUM(Cloc.lines_code) + fn.SUM(Cloc.lines_comment)).alias(
                "lines_total",
            ),
        )
        .where(Cloc.scan == scan)
        .dicts()
        .get()
    )
    result: Sns = Sns(**query)

    # Convert to percentage of total:
    if result.lines_total:
        result.lines_blank_p = (result.lines_blank / result.lines_total) * 100.0
        result.lines_code_p = (result.lines_code / result.lines_total) * 100.0
        result.lines_comment_p = (result.lines_comment / result.lines_total) * 100.0
        result.lines_total_p = result.lines_blank_p + result.lines_code_p + result.lines_comment_p
    else:
        result.lines_blank_p = None
        result.lines_code_p = None
        result.lines_comment_p = None
        result.lines_total_p = None

    # Find the number of files
    result.files_total = (
        Cloc.select(fn.COUNT(Cloc.id).alias("files_total"))
        .where(
            Cloc.scan == scan,
        )
        .get()
        .files_total
    )

    # Calculate the "Code Density"
    metric_value = (result.lines_code / (result.lines_code + result.lines_blank)) * 100.0
    result.code_density = score_metric(args, "tools.cloc.code_density", metric_value)

    # Calculate the "Comment Ratio"
    metric_value = result.lines_comment / (result.lines_code + result.lines_comment) * 100.0
    result.comment_ratio = score_metric(args, "tools.cloc.comment_ratio", metric_value)

    # Calculate average lines per file
    metric_value = int(result.lines_code / result.files_total)
    result.avg_lines_per_file = score_metric(args, "tools.cloc.avg_lines_per_file", metric_value)

    return result


def query_cloc_1(args: Namespace, scan: Scan) -> Sns:
    grand_total: Sns = query_cloc_0(args, scan)
    query = (
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
        .dicts()
    )
    rows = [Sns(**row_dict) for row_dict in query]

    # Convert to percentage of total:
    for row in rows:
        row.lines_code_p = (row.lines_code / grand_total.lines_code) * 100.0
        row.lines_blank_p = (row.lines_blank / grand_total.lines_blank) * 100.0
        row.lines_comment_p = (row.lines_comment / grand_total.lines_comment) * 100.0
        row.lines_total_p = (row.lines_total / grand_total.lines_total) * 100.0
    return Sns(rows=rows, grand_total=grand_total)


def query_cloc_2(args: Namespace, scan: Scan) -> Sns:
    grand_total: Sns = query_cloc_0(args, scan)

    query = (
        Cloc.select()
        .where(Cloc.scan == scan)
        .order_by(
            Cloc.directory,
            Cloc.filename,
        )
        .dicts()
    )
    rows = [Sns(**row_dict) for row_dict in query]

    # Calculate the total for each column/attribute:
    column_totals = defaultdict(int)
    for row in rows:
        column_totals["lines_blank"] += row.lines_blank
        column_totals["lines_comment"] += row.lines_comment
        column_totals["lines_code"] += row.lines_code
        row.lines_total = row.lines_blank + row.lines_comment + row.lines_code

    # Convert to percentage of total:
    for row in rows:
        row.lines_code_p = (row.lines_code / column_totals["lines_code"]) * 100.0
        row.lines_comment_p = (row.lines_comment / column_totals["lines_blank"]) * 100.0
        row.lines_blank_p = (row.lines_blank / column_totals["lines_code"]) * 100.0
        row.lines_total_p = (row.lines_total / grand_total.lines_total) * 100.0

    return Sns(
        rows=rows,
        column_totals=dict(column_totals),
        grand_total=grand_total,
    )


def query_cloc_h(project: Project, dimension: str = "cloc", last: int = None) -> Sns:
    scans = get_scans_for_project_dimension(project, dimension, last=last)

    ################################################################################################
    # Look through to the internal summary.
    ################################################################################################
    rows = list()
    for scan in scans:
        if not scan.summary:
            continue
        row = Sns(timestamp=scan.as_of, git_commit_message=scan.git_commit_message)
        for attr in ("lines_blank", "lines_code", "lines_comment", "lines_total"):
            setattr(row, attr, scan.summary.get(attr, 0))
        rows.append(row)

    timestamps = [row.timestamp for row in rows]
    messages = {row.timestamp: row.git_commit_message for row in rows}

    ################################################################################################
    # Transpose (to get timestamps *across* instead of down and calculate grand totals)
    ################################################################################################
    transposed = defaultdict(lambda: defaultdict(dict))
    grand_totals = defaultdict(int)
    for row in rows:
        # fmt: off
        transposed["Code"    ][row.timestamp] = row.lines_code
        transposed["Comment" ][row.timestamp] = row.lines_comment
        transposed["Blank"   ][row.timestamp] = row.lines_blank
        transposed["Total"   ][row.timestamp] = row.lines_total
        # fmt: on

        # Calculate grand totals for each timestamp as we go
        grand_totals[row.timestamp] += row.lines_total

    roc = dict()
    for attr in ("Code", "Comment", "Blank", "Total"):
        l_timestamps = sorted(transposed[attr].keys())
        if len(l_timestamps) > 1:
            ts_penultimate, ts_last = l_timestamps[-2:]
            roc[attr] = rate_of_change_percentage(
                transposed[attr][ts_penultimate],
                transposed[attr][ts_last],
            )
        else:
            roc[attr] = 0.00
    if len(timestamps) > 1:
        l_timestamps = sorted(timestamps)
        ts_penultimate, ts_last = timestamps[-2:]
        roc["grand_total"] = rate_of_change_percentage(
            grand_totals[ts_penultimate],
            grand_totals[ts_last],
        )
    else:
        roc["grand_total"] = 0.00

    adgs = dict()
    if len(timestamps) > 1:
        days = days_between(timestamps[0], timestamps[-1])
        # fmt: off
        adgs["lines_code"   ] = (rows[-1].lines_code    - rows[0].lines_code   ) / days
        adgs["lines_comment"] = (rows[-1].lines_comment - rows[0].lines_comment) / days
        adgs["lines_blank"  ] = (rows[-1].lines_blank   - rows[0].lines_blank  ) / days
        adgs["lines_total"  ] = (rows[-1].lines_total   - rows[0].lines_total  ) / days
        # fmt: on

    return Sns(
        timestamps=timestamps,
        messages=messages,
        rows=rows,
        transposed=transposed,
        grand_totals=grand_totals,
        roc=roc,
        adgs=adgs,
    )


def query_cloc_f(args: Namespace, scan: Scan) -> list[tuple[str, int]]:
    """Calculate histogram buckets over filesize."""
    buckets = args.config.get("tools.cloc.histogram_file_size.buckets")
    bucket_breaks = [level["min"] for level in buckets]

    # Calculate file density histogram
    query = Cloc.select().where(Cloc.scan == scan)
    file_sizes = [row.lines_code + row.lines_comment + row.lines_blank for row in query]
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
