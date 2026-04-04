"""..."""

import logging
from argparse import Namespace
from types import SimpleNamespace as Sns

import peewee as pw
from peewee import fn, JOIN

from qyx.constants import ViewContext as Vc
from qyx.tools._models_ import BaseModel, Project, Scan
from qyx.tools.common import get_loc, get_scans_for_project_dimension
from qyx.utils import rate_of_change_percentage
from qyx.utils.caching import query_cache
from qyx.utils.scoring import score_metric

log = logging.getLogger(__name__)


class Ruff(BaseModel):
    """..."""

    # fmt: off
    id        = pw.AutoField()
    scan      = pw.ForeignKeyField(Scan, on_delete="CASCADE")
    directory = pw.CharField() # eg. src/qyx/  (Relative to project's root!)
    filename  = pw.CharField() # eg. foo.py
    line      = pw.IntegerField()
    column    = pw.IntegerField()
    rule_code = pw.CharField() # eg. E302, PLC123 etc.
    message   = pw.CharField()
    url       = pw.CharField()
    # fmt: on

    class Meta:
        """..."""

        table_name = "tool_ruff"
        indexes = ((("scan", "directory", "filename", "line", "column", "rule_code"), True),)


@query_cache
def query_ruff_0(args: Namespace, scan: Scan, dimension: str = "ruff", context: Vc = Vc.TOOL_HOME) -> Sns:
    """Calculate summary ruff metrics."""
    query = (
        Ruff.select(
            fn.COUNT(Ruff.id).alias("count"),
        )
        .where(Ruff.scan == scan)
        .dicts()
        .first()
    )
    result: Sns = Sns(**query)
    if lines_of_code := get_loc(args, scan.request.project):
        result = _derived_violations_per_kloc(args, lines_of_code, result)
        result = _derived_weighted_violations_per_kloc(args, lines_of_code, result, scan)
    else:
        log.warning("Sorry, unable to calculate derived Ruff metrics as we don't have any LOC metrics yet!")
    return result


@query_cache
def query_ruff_1(scan: Scan) -> Sns:
    from qyx.tools.ruff import get_ruff_rule_name

    query = (
        Ruff.select(
            Ruff.rule_code,
            fn.COUNT(Ruff.id).alias("count"),
        )
        .where(
            Ruff.scan == scan,
        )
        .group_by(
            Ruff.rule_code,
        )
        .order_by(
            fn.COUNT(Ruff.id).desc(),
        )
        .dicts()
    )
    # Add another attribute onto to each result for nicer reporting.
    rows = [Sns(**row_dict) for row_dict in query]
    for row in rows:
        row.rule_name = get_ruff_rule_name(row.rule_code).title()
    return Sns(rows=rows)


@query_cache
def query_ruff_2(scan: Scan) -> Sns:
    query = Ruff.select().order_by(Ruff.rule_code, Ruff.directory, Ruff.filename).dicts()
    return Sns(rows=[Sns(**row_dict) for row_dict in query])


@query_cache
def query_ruff_h(project: Project, last: int = None) -> Sns:
    # NOTE: This seems a bit backward here as we're querying from Scan and joining the Ruff table.
    # We do this as there are valid cases when there are NO Ruff table entries for a particular
    # scan. We still want the timestamp back with a Ruff count of *0*.
    scans = get_scans_for_project_dimension(project, "ruff", last=last)
    rows = (
        Scan.select(
            Scan.as_of.alias("timestamp"),
            Scan.git_commit_message.alias("message"),
            fn.COUNT(Ruff.id).alias("count"),
        )
        .join(Ruff, JOIN.LEFT_OUTER)
        .where(
            Scan.id.in_([scan.id for scan in scans]),
        )
        .group_by(Scan.as_of)
        .order_by(Scan.as_of)
        .objects()
    )
    timestamps = [row.timestamp for row in rows]
    messages = {row.timestamp: row.message for row in rows}

    ################################################################################################
    # Transpose (to get timestamps *across* instead of down and calculate grand totals)
    ################################################################################################
    transposed = {row.timestamp: row.count for row in rows}

    # Calculate ROC if we can..
    roc = 0.00
    if len(timestamps) > 1:
        value_2 = transposed.get(timestamps[-2])
        value_1 = transposed.get(timestamps[-1])
        if value_2 is not None and value_1 is not None:
            roc = rate_of_change_percentage(value_2, value_1)

    return Sns(timestamps=timestamps, messages=messages, transposed=transposed, roc=roc)


def _derived_violations_per_kloc(args: Namespace, lines_of_code: int, result: Sns):
    """Calculate simple violations per thousand loc (not including comments and blank lines)."""
    if not lines_of_code or not result.count:
        result.violations_per_kloc = None
        return result

    metric_value = (result.count / lines_of_code) * 1000
    result.violations_per_kloc = score_metric(
        args,
        "tools.ruff.violations_per_kloc",
        metric_value,
    )
    return result


def _derived_weighted_violations_per_kloc(args: Namespace, lines_of_code: int, result: Sns, scan: Scan):
    """Calculate *weighted* violations per thousand loc (not including comments and blank lines)."""
    violations_by_severity = __query_counts_by_rule_code_prefix(scan)
    if not lines_of_code or not violations_by_severity:
        result.weighted_violations_per_kloc = None
        return result
    weights = args.config.get("tools.ruff.weighted_violations_per_kloc.weights")
    weighted_score = sum(violations_by_severity.get(code, 0) * weight for code, weight in weights.items())
    metric_value = (weighted_score / lines_of_code) * 1000
    result.weighted_violations_per_kloc = score_metric(
        args,
        "tools.ruff.weighted_violations_per_kloc",
        metric_value,
    )
    return result


def __query_counts_by_rule_code_prefix(scan: Scan) -> dict[str, int]:
    """Return the count of ruff results for the scan by rule code prefix."""
    rows = (
        Ruff.select(
            fn.SUBSTR(Ruff.rule_code, 1, 1).alias("rule_prefix"),
            fn.COUNT(Ruff.id).alias("count"),
        )
        .where(
            Ruff.scan == scan,
        )
        .group_by(
            fn.SUBSTR(Ruff.rule_code, 1, 1),
            Ruff.rule_code,
        )
    )
    return {row.rule_prefix: row.count for row in rows}
