"""..."""

import logging
from argparse import Namespace
from types import SimpleNamespace as Sns

from peewee import fn, CharField, IntegerField, JOIN

from qyx.constants import ViewContext as Vc
from qyx.tools.base import BaseResultsModel, Project, Scan
from qyx.tools.common import get_loc, get_scans_for_project_analysis
from qyx.utils import rate_of_change_percentage
from qyx.utils.caching import query_cache
from qyx.utils.scoring import score_metric

log = logging.getLogger(__name__)


class Ty(BaseResultsModel):
    """..."""

    # fmt: off
    line        = IntegerField()
    column      = IntegerField()
    check_name  = CharField() # Eg. invalid-argument-type, unresolved-attribute etc.")
    description = CharField()
    severity    = CharField() # Eg. major, ... ?
    fingerprint = CharField()
    # fmt: on

    class Meta:
        """..."""

        table_name = "ty"
        indexes = ((("scan", "directory", "filename", "fingerprint"), True),)


@query_cache
def query_ty_0(args: Namespace, scan: Scan, context: Vc = Vc.TOOL_HOME) -> Sns:
    query = (
        Ty.select(
            fn.COUNT(Ty.id).alias("count"),
        )
        .where(Ty.scan == scan)
        .dicts()
        .first()
    )
    result: Sns = Sns(**query)

    if lines_of_code := get_loc(args, scan.request.project):
        result = _derived_violations_per_kloc(args, lines_of_code, result)
        result = _derived_weighted_violations_per_kloc(args, lines_of_code, result, scan)
    else:
        log.warning("Sorry, unable to calculate derived Ty metrics as we don't have any LOC metrics yet!")

    return result


@query_cache
def query_ty_1(scan: Scan) -> Sns:
    query = (
        Ty.select(
            Ty.check_name,
            fn.COUNT(Ty.id).alias("count"),
        )
        .where(
            Ty.scan == scan,
        )
        .group_by(
            Ty.check_name,
        )
        .order_by(
            fn.COUNT(Ty.id).desc(),
        )
        .dicts()
    )
    return Sns(rows=[Sns(**row_dict) for row_dict in query])


@query_cache
def query_ty_2(scan: Scan):
    query = (
        Ty.select(
            Ty.check_name,
            Ty.directory,
            fn.COUNT(Ty.id).alias("count"),
        )
        .where(
            Ty.scan == scan,
        )
        .group_by(
            Ty.check_name,
            Ty.directory,
        )
        .order_by(
            fn.COUNT(Ty.id).desc(),
        )
        .dicts()
    )
    return Sns(rows=[Sns(**row_dict) for row_dict in query])


@query_cache
def query_ty_3(scan: Scan) -> Sns:
    query = (
        Ty.select()
        .where(
            Ty.scan == scan,
        )
        .order_by(
            Ty.directory,
            Ty.filename,
            Ty.check_name,
        )
        .dicts()
    )
    return Sns(rows=[Sns(**row_dict) for row_dict in query])


@query_cache
def query_ty_h(project: Project, last: int = None) -> Sns:
    # NOTE: This seems a bit backward here as we're querying from Scan and joining the Ty table.
    # We do this as there are valid cases when there are NO Ty table
    # entries for a particular scan. We still want the timestamp back
    # with a Ty count of *0*.
    scans = get_scans_for_project_analysis(project, "ty", last=last)
    query = (
        Scan.select(
            Scan.as_of.alias("timestamp"),
            Scan.git_commit_message.alias("message"),
            fn.COUNT(Ty.id).alias("count"),
        )
        .join(Ty, JOIN.LEFT_OUTER)
        .where(
            Scan.id.in_(scans),
        )
        .group_by(Scan.as_of)
        .order_by(Scan.as_of)
        .objects()
    )
    timestamps = [row.timestamp for row in query]
    messages = {row.timestamp: row.message for row in query}

    ################################################################################################
    # Transpose (to get timestamps *across* instead of down and calculate grand totals)
    ################################################################################################
    transposed = {row.timestamp: row.count for row in query}

    # Calculate ROC if we can..
    roc = 0.00
    if len(timestamps) > 1:
        value_2 = transposed.get(timestamps[-2])
        value_1 = transposed.get(timestamps[-1])
        if value_2 is not None and value_1 is not None:
            if not (roc := rate_of_change_percentage(value_2, value_1)):
                log.debug(f"{timestamps[-2]=}:{value_2=} {timestamps[-1]=}:{value_1=}")

    return Sns(timestamps=timestamps, messages=messages, transposed=transposed, roc=roc)


def _derived_violations_per_kloc(args: Namespace, lines_of_code: int, result: Sns) -> Sns:
    """Calculate simple violations per thousand loc (not including comments and blank lines)."""
    if not lines_of_code or not result.count:
        result.violations_per_kloc = None
        return result

    metric_value = (result.count / lines_of_code) * 1000
    result.violations_per_kloc = score_metric(args, "tools.ty.violations_per_kloc", metric_value)
    return result


def _derived_weighted_violations_per_kloc(args: Namespace, lines_of_code: int, result: Sns, scan: Scan) -> Sns:
    """Calculate *weighted* violations per thousand loc (not including comments and blank lines)."""
    checks_by_check_name = query_ty_1(scan)
    if not lines_of_code or not checks_by_check_name.rows:
        result.weighted_violations_per_kloc = None
        return result

    weights_by_category = args.config.get("tools.ty.weighted_violations_per_kloc.weights")
    checknames_by_category = args.config.get("tools.ty.weighted_violations_per_kloc.categories")
    category_by_checkname = {check: category for category, checks in checknames_by_category.items() for check in checks}

    weighted_scores = []
    for check_and_count in checks_by_check_name.rows:  # eg. "invalid-parameter-default" & 50
        try:
            category = category_by_checkname[check_and_count.check_name]  # eg. medium
        except KeyError:
            log.error(
                f"Sorry, unable to categorise ty check type of {check_and_count.check_name}, "
                "check your configuration file!"
            )
            continue
        weight = weights_by_category[category]  # eg. 3.0
        score = check_and_count.count * weight  # eg. 150.0
        weighted_scores.append(score)
    weighted_score = sum(weighted_scores)

    metric_value = (weighted_score / lines_of_code) * 1000

    result.weighted_violations_per_kloc = score_metric(args, "tools.ty.weighted_violations_per_kloc", metric_value)
    return result
