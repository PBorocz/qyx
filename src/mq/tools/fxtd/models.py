"""Fxtd Models and Queries."""

import logging
from argparse import Namespace
from collections import defaultdict

from peewee import fn, CharField, IntegerField, JOIN

from mq.constants import ReportLevel
from mq.tools.base import BaseResultsModel, Project, Scan
from mq.tools.common import get_loc, get_scans_for_pta
from mq.utils import rate_of_change_percentage
from mq.utils.scoring import score_metric


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


def query(
    args: Namespace,
    level: str,
    project: Project = None,
    scan: Scan = None,
    last: int = None,
) -> Fxtd:
    match level.lower():
        case ReportLevel.SUMMARY:
            return _query_0(args, scan)
        case ReportLevel.DIRECTORY:
            return _query_1(args, scan)
        case ReportLevel.FILE:
            return _query_2(args, scan)
        case ReportLevel.DERIVED:
            return _query_d(args, project, scan)
        case ReportLevel.HISTORY:
            return _query_h(args, project, last)


def _query_0(args: Namespace, scan: Scan):
    return (
        Fxtd.select(
            Fxtd.type,
            fn.COUNT(Fxtd.id).alias("count"),
        )
        .where(Fxtd.scan == scan)
        .group_by(Fxtd.type)
        .order_by(fn.COUNT(Fxtd.id).desc())
    )


def _query_1(args: Namespace, scan: Scan):
    return (
        Fxtd.select(
            Fxtd.directory,
            Fxtd.type,
            fn.COUNT(Fxtd.id).alias("count"),
        )
        .where(Fxtd.scan == scan)
        .group_by(Fxtd.directory, Fxtd.type)
        .order_by(fn.COUNT(Fxtd.id).desc())
    )


def _query_2(args: Namespace, scan: Scan):
    return (
        Fxtd.select()
        .where(Fxtd.scan == scan)
        .order_by(
            Fxtd.directory,
            Fxtd.filename,
            Fxtd.line,
        )
    )


def _query_h(args: Namespace, project: Project, last: int = None):
    scans = get_scans_for_pta(project, tool="fxtd", last=last)
    rows = (
        Scan.select(
            Scan.as_of.alias("timestamp"),
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

    ################################################################################################
    # Transpose (to get timestamps *across* instead of down and calculate grand totals)
    ################################################################################################
    timestamps = list({row.timestamp for row in rows if row.count})
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

    return timestamps, transposed, rocs


def _query_d(args: Namespace, project: Project, fxtd_scan: Scan):
    """Calculate derived fxtd metrics."""
    if not (lines_of_code := get_loc(args, project)):
        log.warning("Sorry, unable to calculate derived Fxtd metrics as we don't have any LOC metrics yet!")
        return None, None

    score_by_type = _query_0(args, fxtd_scan)
    if score_by_type:  # Perfectly valid to not have any!
        score_by_type = _by_type_per_kloc(args, lines_of_code, score_by_type)
        composite_weighted_score = _composite_per_kloc(args, lines_of_code, score_by_type)
        return score_by_type, composite_weighted_score
    else:
        return None, None


def _by_type_per_kloc(args: Namespace, lines_of_code: int, rows):
    """Calculate score of FixMe issues for a particular "type" per thousand sloc."""
    for row in rows:
        metric_value = (row.count / lines_of_code) * 1000
        row.fxtd_d = score_metric(args, "tools.fxtd.by_type_per_kloc", metric_value)
    return rows


def _composite_per_kloc(args: Namespace, lines_of_code: int, rows) -> Namespace:
    """Calculate composite_weighted score of FixMe issues per thousand loc (not including comments and blank lines)."""
    weights = args.config.get("tools.fxtd.composite_weighted_per_kloc.weights")
    weighted_score = sum([row.count * weights.get(row.type.upper(), 1) for row in rows])
    metric_value = (weighted_score / lines_of_code) * 1000
    return score_metric(args, "tools.fxtd.composite_weighted_per_kloc", metric_value)
