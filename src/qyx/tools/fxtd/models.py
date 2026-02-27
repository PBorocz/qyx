"""Fxtd Models and Queries."""

import logging
from argparse import Namespace
from collections import defaultdict
from types import SimpleNamespace as Sns

from peewee import fn, CharField, IntegerField, JOIN

from qyx.constants import ViewContext as Vc
from qyx.tools.base import BaseResultsModel, Project, Scan
from qyx.tools.common import get_loc, get_scans_for_project_analysis
from qyx.utils import rate_of_change_percentage
from qyx.utils.caching import query_cache
from qyx.utils.scoring import score_metric


log = logging.getLogger(__name__)


class Fxtd(BaseResultsModel):
    """..."""

    # fmt: off
    type    = CharField()    # eg. "FIXME", "TODO", etc.
    message = CharField()    # eg FIXME: lorem ipsum...
    line    = IntegerField() # eg. 25
    # fmt: on

    class Meta:
        """..."""

        table_name = "fxtd"
        indexes = ((("scan", "directory", "filename", "line"), True),)


@query_cache
def query_0(args: Namespace, project: Project, scan: Scan, context: Vc = Vc.TOOL_HOME) -> Sns:
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

    if not (lines_of_code := get_loc(args, project)):
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
def query_1(scan: Scan) -> Sns:
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
def query_2(scan: Scan) -> Sns:
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
def query_h(project: Project, last: int = None) -> Sns:
    scans = get_scans_for_project_analysis(project, "fxtd", last=last)
    rows = (
        Scan.select(
            Scan.as_of.alias("timestamp"),
            Scan.git_commit_message.alias("message"),
            Fxtd.type,
            fn.COUNT(Fxtd.id).alias("count"),
        )
        .join(Fxtd, JOIN.LEFT_OUTER)
        .where(Scan.id.in_(scans))
        .group_by(
            Scan.as_of,
            Fxtd.type,
        )
        .order_by(Scan.as_of)
        .objects()
    )
    timestamps = list({row.timestamp for row in rows if row.count})
    messages = {row.timestamp: row.message for row in rows}

    ################################################################################################
    # Transpose (to get timestamps *across* instead of down and calculate grand totals)
    ################################################################################################
    transposed = defaultdict(dict)
    for row in rows:
        if row.count:
            transposed[row.type][row.timestamp] = row.count

    # Calculate ROC if we can..
    rocs = dict()
    if len(timestamps) > 1:
        for type_, values_by_timestamp in transposed.items():
            value_2 = values_by_timestamp.get(timestamps[-2])
            value_1 = values_by_timestamp.get(timestamps[-1])
            if value_2 is not None and value_1 is not None:
                rocs[type_] = rate_of_change_percentage(value_2, value_1)

    return Sns(timestamps=timestamps, messages=messages, transposed=transposed, rocs=rocs)
