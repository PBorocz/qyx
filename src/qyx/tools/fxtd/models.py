"""Fxtd Models and Queries."""

import logging
from argparse import Namespace
from collections import defaultdict
from types import SimpleNamespace as Sns

import peewee as pw
from peewee import fn

from qyx.constants import ViewContext as Vc
from qyx.tools._models_ import BaseModel, Project, Scan
from qyx.tools.common import get_loc, get_scans_for_project_dimension
from qyx.utils import rate_of_change_percentage
from qyx.utils.caching import query_cache
from qyx.utils.scoring import score_metric


log = logging.getLogger(__name__)


class Fxtd(BaseModel):
    """..."""

    # fmt: off
    id        = pw.AutoField()
    scan      = pw.ForeignKeyField(Scan, on_delete="CASCADE")
    directory = pw.CharField(help_text="eg. src/qyx/") # Relative to project's root!
    filename  = pw.CharField(help_text="eg. foo.py")
    type      = pw.CharField()    # eg. "FIXME", "TODO", etc.
    message   = pw.CharField()    # eg FIXME: lorem ipsum...
    line      = pw.IntegerField() # eg. 25
    # fmt: on

    class Meta:
        """..."""

        table_name = "tool_fxtd"
        indexes = ((("scan", "directory", "filename", "line"), True),)


@query_cache
def query_fxtd_0(args: Namespace, scan: Scan, dimension: str = "fxtd", context: Vc = Vc.TOOL_HOME) -> Sns:
    """Calculate summary level fxtd metrics."""
    query = (
        Fxtd.select(
            Fxtd.type,
            fn.COUNT(Fxtd.id).alias("count"),
        )
        .where(Fxtd.scan == scan)
        .group_by(Fxtd.type)
        .order_by(fn.COUNT(Fxtd.id).desc())
        .dicts()
    )
    if not query:  # Perfectly valid to not have any!
        return Sns(rows=[])

    rows = [Sns(**row_dict) for row_dict in query]
    grand_total = sum([row.count for row in rows])

    if not (lines_of_code := get_loc(args, scan.request.project)):
        log.warning("Sorry, unable to calculate derived 'fxtd' metrics as we don't have any lines-of-code yet!")
        return Sns(rows=rows, grand_total=grand_total)

    # Calculate score of entries per kLOC (sloc)"""
    for row in rows:
        metric_value = (row.count / lines_of_code) * 1000
        row.metric = score_metric(args, "tools.fxtd.by_type_per_kloc", metric_value)

    # Calculate *composite weighted* score of entries per kLOC (not including comments and blank lines)"""
    weights = args.config.get("tools.fxtd.composite_weighted_per_kloc.weights")
    weighted_score = sum([row.count * weights.get(row.type.upper(), 1) for row in rows])
    metric_value = (weighted_score / lines_of_code) * 1000
    metric_composite_weighted = score_metric(args, "tools.fxtd.composite_weighted_per_kloc", metric_value)
    return Sns(rows=rows, grand_total=grand_total, metric_composite_weighted=metric_composite_weighted)


@query_cache
def query_fxtd_1(scan: Scan) -> Sns:
    query = (
        Fxtd.select(
            Fxtd.directory,
            Fxtd.type,
            fn.COUNT(Fxtd.id).alias("count"),
        )
        .where(Fxtd.scan == scan)
        .group_by(Fxtd.directory, Fxtd.type)
        .order_by(fn.COUNT(Fxtd.id).desc())
        .dicts()
    )
    rows = [Sns(**row_dict) for row_dict in query]
    grand_total = sum([row.count for row in rows])
    return Sns(rows=rows, grand_total=grand_total)


@query_cache
def query_fxtd_2(scan: Scan) -> Sns:
    query = (
        Fxtd.select()
        .where(Fxtd.scan == scan)
        .order_by(
            Fxtd.directory,
            Fxtd.filename,
            Fxtd.line,
        )
        .dicts()
    )
    rows = [Sns(**row_dict) for row_dict in query]
    return Sns(rows=rows)


@query_cache
def query_fxtd_h(project: Project, dimension: str = "fxtd", last: int = None) -> Sns:
    scans = get_scans_for_project_dimension(project, dimension, last=last)

    timestamps = [fxtd.as_of for fxtd in scans if fxtd.summary]
    messages = {fxtd.as_of: fxtd.git_commit_message for fxtd in scans}

    transposed = defaultdict(dict)
    for scan in scans:
        for type_, count in dict(scan.summary).items():
            if count:
                transposed[type_][scan.as_of] = count

    # Calculate ROC if we can..
    rocs = dict()
    if len(timestamps) > 1:
        for type_, values_by_timestamp in transposed.items():
            l_timestamps = sorted(values_by_timestamp.keys())
            ts_penultimate, ts_last = l_timestamps[-2:]
            value_2 = values_by_timestamp.get(ts_penultimate)
            value_1 = values_by_timestamp.get(ts_last)
            if value_1 and value_2:
                rocs[type_] = rate_of_change_percentage(value_2, value_1)

    return Sns(timestamps=timestamps, messages=messages, transposed=transposed, rocs=rocs)
