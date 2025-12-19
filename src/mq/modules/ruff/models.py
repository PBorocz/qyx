"""..."""

from argparse import Namespace
from collections import defaultdict

from peewee import fn, CharField, IntegerField

from mq.modules.models import BaseModuleModel, Project, Run
from mq.modules.ruff import MODULE


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


def query_summary(args: Namespace, run: Run) -> Ruff:
    return Ruff.select(fn.COUNT(Ruff.id).alias("count")).where(Ruff.run == run)


def query_detail(args: Namespace, run: Run) -> Ruff:
    return (
        Ruff.select(Ruff.rule_code, Ruff.message, fn.COUNT(Ruff.id).alias("count"))
        .where(Ruff.run == run)
        .group_by(Ruff.rule_code)
        .order_by(fn.COUNT(Ruff.id).desc())
    )


def query_full(args: Namespace, run: Run) -> Ruff:
    return Ruff.select().where(Ruff.run == run).order_by(Ruff.filename, Ruff.rule_code)


def query_history(args: Namespace, project: Project) -> Run:
    runs_for_project_module = (
        Run.select(Run.id)
        .where(Run.project == project.id, Run.module == MODULE)
        .order_by(Run.timestamp.desc())
        .limit(args.last)
    )

    ################################################################################################
    # Query
    ################################################################################################
    rows = (
        Ruff.select(
            Run.timestamp.alias("timestamp"),
            Ruff.rule_code.alias("rule_code"),
            Ruff.message.alias("message"),
        )
        .where(Project.id == project.id, Run.id.in_(runs_for_project_module))
        .join(Run)
        .join(Project)
        .order_by(Run.timestamp)
        .objects()
    )
    messages = {row.rule_code: row.message for row in rows}

    ################################################################################################
    # Transpose (to get timestamps *across* instead of down and calculate grand totals)
    ################################################################################################
    transposed = defaultdict(lambda: defaultdict(int))
    grand_totals = defaultdict(int)
    for row in rows:
        transposed[row.rule_code][row.timestamp] += 1
        grand_totals[row.timestamp] += 1

    return rows, messages, transposed, grand_totals
