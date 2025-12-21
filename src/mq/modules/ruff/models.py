"""..."""

from argparse import Namespace

from peewee import fn, CharField, IntegerField

from mq.modules.base import BaseModuleModel, Project, Run
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
        indexes = ((("run", "dir", "filename", "line", "column", "rule_code"), True),)


def query(args: Namespace, level: str, run: Run = None, project: Project = None) -> Ruff:
    match level.lower():
        case "0":
            return Ruff.select(fn.COUNT(Ruff.id).alias("count")).where(Ruff.run == run)

        case "1":
            return (
                Ruff.select(Ruff.rule_code, Ruff.message, fn.COUNT(Ruff.id).alias("count"))
                .where(Ruff.run == run)
                .group_by(Ruff.rule_code)
                .order_by(fn.COUNT(Ruff.id).desc())
            )

        case "2":
            return Ruff.select().where(Ruff.run == run).order_by(Ruff.filename, Ruff.rule_code)

        case "h" | "history":
            # FIXME: Add support for parsing args.options to pull out last:<d>
            args_last = 2
            runs = (
                Run.select()
                .where(
                    Run.project == project.id,
                    Run.module == MODULE,
                )
                .order_by(Run.timestamp.desc())
                .limit(args_last)
            )

            ################################################################################################
            # Query
            ################################################################################################
            rows = (
                Ruff.select(
                    Run.timestamp.alias("timestamp"),
                    fn.COUNT(Ruff.id).alias("count"),
                )
                .join(Run)
                .where(
                    Run.id.in_(runs),
                )
                .group_by(Run.timestamp)
                .order_by(Run.timestamp)
                .objects()
            )
            timestamps = [result.timestamp for result in rows]

            ################################################################################################
            # Transpose (to get timestamps *across* instead of down and calculate grand totals)
            ################################################################################################
            transposed = {row.timestamp: row.count for row in rows}

            roc = rate_of_change_percentage(
                transposed[timestamps[-2]],
                transposed[timestamps[-1]],
            )

            return timestamps, transposed, roc
