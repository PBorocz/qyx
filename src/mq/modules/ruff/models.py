"""..."""

from argparse import Namespace

from peewee import fn, CharField, IntegerField, JOIN

from mq.modules.base import BaseModuleModel, Project, Scan
from mq.modules.ruff import MODULE
from mq.utils import rate_of_change_percentage


class Ruff(BaseModuleModel):
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
        indexes = ((("scan", "dir", "filename", "line", "column", "rule_code"), True),)


def query(args: Namespace, level: str, scan: Scan = None, project: Project = None) -> Ruff:
    match level.lower():
        case "0":
            return Ruff.select(
                fn.COUNT(Ruff.id).alias("count"),
            ).where(
                Ruff.scan == scan,
            )

        case "1":
            return (
                Ruff.select(
                    Ruff.rule_code,
                    Ruff.message,
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
                    Ruff.dir,
                    Ruff.filename,
                )
            )

        case "h" | "history":
            scans = (
                Scan.select()
                .where(
                    Scan.project == project.id,
                    Scan.module == MODULE,
                )
                .order_by(
                    Scan.timestamp.desc(),
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
            # run. We still want the timestamp back with a Ruff count of *0*.
            rows = (
                Scan.select(
                    Scan.timestamp.alias("timestamp"),
                    fn.COUNT(Ruff.id).alias("count"),
                )
                .join(Ruff, JOIN.LEFT_OUTER)
                .where(
                    Scan.id.in_(scans),
                )
                .group_by(Scan.timestamp)
                .order_by(Scan.timestamp)
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
