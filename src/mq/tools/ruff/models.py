"""..."""

import logging
from argparse import Namespace

from peewee import fn, CharField, IntegerField, JOIN

from mq.tools.base import BaseResultsModel, Project, Request, Scan
from mq.tools.cloc.models import query as query_cloc
from mq.tools.radon.models import query_raw as query_radon_raw
from mq.utils import rate_of_change_percentage
from mq.utils.scoring import get_nested_config, score_metric

log = logging.getLogger(__name__)


class Ruff(BaseResultsModel):
    """..."""

    # fmt: off
    line      = IntegerField()
    column    = IntegerField()
    rule_code = CharField(help_text="Eg. E302, PLC123 etc.")
    message   = CharField()
    url       = CharField(null=True)
    # fmt: on

    class Meta:
        """..."""

        table_name = "ruff"
        indexes = ((("scan", "directory", "filename", "line", "column", "rule_code"), True),)


def query(
    args: Namespace,
    level: str,
    project: Project = None,
    scan: Scan = None,
    last: int = None,
) -> Ruff:
    match level.lower():
        case "0":
            return _query_0(args, scan)
        case "1":
            return _query_1(args, scan)
        case "2":
            return _query_2(args, scan)
        case "d":
            return _query_d(args, project, scan)
        case "h":
            return _query_h(args, project, last)


def _query_0(args: Namespace, scan: Scan):
    return (
        Ruff.select(
            fn.COUNT(Ruff.id).alias("count"),
        )
        .where(
            Ruff.scan == scan,
        )
        .first()
    )


def _query_1(args: Namespace, scan: Scan):
    return (
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
    )


def _query_2(args: Namespace, scan: Scan):
    return (
        Ruff.select()
        .where(
            Ruff.scan == scan,
        )
        .order_by(
            Ruff.rule_code,
            Ruff.directory,
            Ruff.filename,
        )
    )


def _query_h(args: Namespace, project: Project, last: int = None):
    scans = (
        Scan.select()
        .where(
            Request.project == project,
            Scan.tool == "ruff",
        )
        .join(Request)
        .order_by(
            Scan.as_of.desc(),
        )
    )
    if last:
        scans = scans.limit(last)

    ################################################################################################
    # Query
    ################################################################################################
    # NOTE: This seems a bit backward here as we're querying from Scan and joining the Ruff table.
    # We do this as there are valid cases when there are NO Ruff table entries for a particular
    # scan. We still want the timestamp back with a Ruff count of *0*.
    rows = (
        Scan.select(
            Scan.as_of.alias("timestamp"),
            fn.COUNT(Ruff.id).alias("count"),
        )
        .join(Ruff, JOIN.LEFT_OUTER)
        .where(
            Scan.id.in_(scans),
        )
        .group_by(Scan.as_of)
        .order_by(Scan.as_of)
        .objects()
    )
    timestamps = [row.timestamp for row in rows]

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
            if not (roc := rate_of_change_percentage(value_2, value_1)):
                log.debug(f"{timestamps[-2]=}:{value_2=} {timestamps[-1]=}:{value_1=}")

    return timestamps, transposed, roc


def _query_d(args: Namespace, project: Project, scan: Scan):
    """Calculate derived ruff metrics."""
    cloc_scan = Scan.get_most_recent(project, "cloc", "cloc")
    if cloc_scan:
        result = query_cloc(args, "0", scan=cloc_scan)
        lines_of_code = result.lines_code
    else:
        radon_scan = Scan.get_most_recent(project, "radon", "raw")
        if radon_scan:
            result = query_radon_raw(args, "0", project=project, scan=radon_scan)
            lines_of_code = result.loc
        else:
            log.warning("Sorry, unable to calculate derived Ruff metrics as we don't have an LOC metrics yet!")
            return None

    result = _query_0(args, scan)
    result = _derived_violations_per_kloc(args, lines_of_code, result)
    result = _derived_weighted_violations_per_kloc(args, lines_of_code, result, scan)
    return result


def _derived_violations_per_kloc(args: Namespace, lines_of_code: int, result):
    """Calculate simple violations per thousand loc (not including comments and blank lines)."""
    metric_value = (result.count / lines_of_code) * 1000
    result.violations_per_kloc = score_metric(
        args,
        "tools.ruff.violations_per_kloc",
        metric_value,
    )
    return result


def _derived_weighted_violations_per_kloc(args: Namespace, lines_of_code: int, result, scan: Scan):
    """Calculate *weighted* violations per thousand loc (not including comments and blank lines)."""
    # fmt: off
    weights = {
        "F": 5,  # Pyflakes                (likely bugs, runtime errors)

        "B": 4,  # Flake8                  (bugbear - likely bugs, design issues)
        "S": 4,  # Security issues         (potential vulnerabilities)

        "E": 3,  # Errors                  (PEP8 violations, code correctness)

        "A": 2,  # Flake8                  (builtins - shadowing built-ins)
        "C": 2,  # Complexity (mccabe)     (maintainability)
        "R": 2,  # Refactoring suggestions (maintainability)
        "U": 2,  # Unused code             (dead code)
        "W": 2,  # Warnings                (various issues)

        "D": 1,  # Docstring conventions   (documentation quality)
        "I": 1,  # Import sorting          (organization)
        "N": 1,  # Naming conventions      (readability)
        "P": 1,  # Pylint conventions      (style preferences)
        "Q": 1,  # Quote consistency       (minor style)
        "T": 1,  # Print statements        (debugging leftovers)
    }
    # fmt: off
    violations_by_severity = __query_counts_by_rule_code_prefix(scan)
    weights = get_nested_config(args.config, "tools.ruff.weighted_violations_per_kloc.weights")
    weighted_score = sum(violations_by_severity.get(code, 0) * weight for code, weight in weights.items())
    metric_value = (weighted_score / lines_of_code) * 1000
    result.weighted_violations_per_kloc = score_metric(args,
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
