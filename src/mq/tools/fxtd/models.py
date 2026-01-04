"""Fxtd Models and Queries."""

from argparse import Namespace

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
    args: Namespace,
    level: str,
    project: Project = None,
    scan: Scan = None,
) -> Fxtd:
    match level.lower():
        case "0":
            return Fxtd.select(fn.COUNT(Fxtd.id).alias("count")).where(Fxtd.scan == scan).first()

        case "1":
            return (
                Fxtd.select(
                    Fxtd.type,
                    fn.COUNT(Fxtd.id).alias("count"),
                )
                .where(Fxtd.scan == scan)
                .group_by(Fxtd.type)
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
            scans = (
                Scan.select()
                .where(
                    Request.project == project,
                    Scan.tool == "fxtd",
                )
                .join(Request)
                .order_by(Scan.as_of.desc())
                .limit(args.options.last)
            )

            ################################################################################################
            # Query
            ################################################################################################
            rows = (
                Scan.select(
                    Scan.as_of.alias("timestamp"),
                    fn.COUNT(Fxtd.id).alias("count"),
                )
                .join(Fxtd, JOIN.LEFT_OUTER)
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
            if len(timestamps) > 1:
                roc = rate_of_change_percentage(
                    transposed[timestamps[-2]],
                    transposed[timestamps[-1]],
                )
            else:
                roc = 0.00

            return timestamps, transposed, roc
