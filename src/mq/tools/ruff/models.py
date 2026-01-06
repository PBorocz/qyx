"""..."""

from argparse import Namespace

from peewee import fn, CharField, IntegerField, JOIN

from mq.tools.base import BaseResultsModel, Project, Request, Scan
from mq.utils import rate_of_change_percentage


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
) -> Ruff:
    match level.lower():
        case "0":
            return (
                Ruff.select(
                    fn.COUNT(Ruff.id).alias("count"),
                )
                .where(
                    Ruff.scan == scan,
                )
                .first()
            )

        case "1":
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

        case "2":
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

        case "h" | "history":
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
                .limit(
                    args.options.last,
                )
            )

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
                    roc = rate_of_change_percentage(value_2, value_1)

            return timestamps, transposed, roc
