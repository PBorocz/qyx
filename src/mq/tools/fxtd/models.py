"""Fxtd Models and Queries."""

from argparse import Namespace
from collections import defaultdict

from peewee import fn, CharField, IntegerField, JOIN

from mq.tools.base import BaseResultsModel, Project, Request, Scan
from mq.utils import rate_of_change_percentage


class Fxtd(BaseResultsModel):
    """..."""

    # fmt: off
    # FIXME: Use an enum here?
    line    = IntegerField()  # eg. 25
    type    = CharField()     # eg. "FIXME" or "TODO"
    message = CharField()     # eg FIXME: lorem ipsum...
    # fmt: on

    class Meta:
        """..."""

        table_name = "fxtd"
        indexes = ((("scan", "directory", "filename", "line"), True),)


def query(
    level: str,
    project: Project = None,
    scan: Scan = None,
    last: int = 5,
) -> Fxtd:
    match level.lower():
        case "0":
            return (
                Fxtd.select(
                    Fxtd.type,
                    fn.COUNT(Fxtd.id).alias("count"),
                )
                .where(Fxtd.scan == scan)
                .group_by(Fxtd.type)
                .order_by(fn.COUNT(Fxtd.id).desc())
            )

        case "1":
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

        case "2":
            return (
                Fxtd.select()
                .where(Fxtd.scan == scan)
                .order_by(
                    Fxtd.directory,
                    Fxtd.filename,
                    Fxtd.line,
                )
            )

        case "h" | "history":
            # FIXME: This query is COMMON across a bunch of stuff...
            scans = (
                Scan.select()
                .where(
                    Request.project == project,
                    Scan.tool == "fxtd",
                )
                .join(Request)
                .order_by(Scan.as_of.desc())
                .limit(last)
            )

            ################################################################################################
            # Query
            ################################################################################################
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
            timestamps = list({result.timestamp for result in rows})
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
