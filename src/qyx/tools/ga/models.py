"""..."""

import logging
from argparse import Namespace
from types import SimpleNamespace as Sns

import peewee as pw
from playhouse.sqlite_ext import JSONField

# from peewee import fn

from qyx.constants import ViewContext as Vc
from qyx.tools._models_ import BaseModel, Scan

# from qyx.tools.common import get_loc, get_scans_for_project_dimension
# from qyx.utils import rate_of_change_percentage
from qyx.utils.caching import query_cache
# from qyx.utils.scoring import score_metric

log = logging.getLogger(__name__)


class Ga(BaseModel):
    """Git Analytics base model."""

    # fmt: off
    id                = pw.AutoField()
    scan              = pw.ForeignKeyField(Scan, on_delete="CASCADE")
    authorship        = JSONField(null=True)
    bug_commits       = JSONField(null=True)
    commit_frequency  = JSONField(null=True)
    emergency_commits = JSONField(null=True)
    file_churn        = JSONField(null=True)
    # fmt: on

    class Meta:
        """..."""

        table_name = "tool_ga"
        indexes = ((("scan",), True),)


def query_ga_0(args: Namespace, scan: Scan, dimension: str = None, context: Vc = Vc.TOOL_HOME) -> Sns:
    if ga_ := Ga.select().where(Ga.scan == scan).dicts().first():
        if dimension:
            return Sns(**{dimension: ga_.get(dimension)})
        else:
            return Sns(**ga_)
    return Sns()


# @query_cache
# def query_ga_1(scan: Scan) -> Sns:
#     query = (
#         Ga.select(
#             Ga.check_name,
#             fn.COUNT(Ga.id).alias("count"),
#         )
#         .where(
#             Ga.scan == scan,
#         )
#         .group_by(
#             Ga.check_name,
#         )
#         .order_by(
#             fn.COUNT(Ga.id).desc(),
#         )
#         .dicts()
#     )
#     return Sns(rows=[Sns(**row_dict) for row_dict in query])


# @query_cache
# def query_ga_2(scan: Scan):
#     query = (
#         Ga.select(
#             Ga.check_name,
#             Ga.directory,
#             fn.COUNT(Ga.id).alias("count"),
#         )
#         .where(
#             Ga.scan == scan,
#         )
#         .group_by(
#             Ga.check_name,
#             Ga.directory,
#         )
#         .order_by(
#             fn.COUNT(Ga.id).desc(),
#         )
#         .dicts()
#     )
#     return Sns(rows=[Sns(**row_dict) for row_dict in query])


# @query_cache
# def query_ga_3(scan: Scan) -> Sns:
#     query = (
#         Ga.select()
#         .where(
#             Ga.scan == scan,
#         )
#         .order_by(
#             Ga.directory,
#             Ga.filename,
#             Ga.check_name,
#         )
#         .dicts()
#     )
#     return Sns(rows=[Sns(**row_dict) for row_dict in query])


# @query_cache
# def query_ga_h(project: Project, dimension: str = "ty", last: int = None) -> Sns:
#     # NOTE: This seems a bit backward here as we're querying from Scan and joining the Ga table.
#     # We do this as there are valid cases when there are NO Ga table
#     # entries for a particular scan. We still want the timestamp back
#     # with a Ga count of *0*.
#     scans = get_scans_for_project_dimension(project, dimension, last=last)
#     timestamps = [scan.as_of for scan in scans]
#     messages = {scan.as_of: scan.git_commit_message for scan in scans}

#     ################################################################################################
#     # Transpose (to get timestamps *across* instead of down and calculate grand totals)
#     ################################################################################################
#     transposed = dict()
#     for scan in scans:
#         if scan.summary:
#             transposed[scan.as_of] = dict(scan.summary).get("number_of_violations", 0)

#     # Calculate ROC if we can..
#     roc = 0.00
#     if len(timestamps) > 1:
#         l_timestamps = sorted(timestamps)
#         ts_penultimate, ts_last = l_timestamps[-2:]
#         value_2 = transposed[ts_penultimate]
#         value_1 = transposed[ts_last]
#         if value_2 and value_1:
#             roc = rate_of_change_percentage(value_2, value_1)

#     return Sns(timestamps=timestamps, messages=messages, transposed=transposed, roc=roc)
