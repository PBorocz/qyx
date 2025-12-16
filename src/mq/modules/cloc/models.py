"""..."""

from argparse import Namespace
from collections import defaultdict

from peewee import fn, IntegerField

from mq.modules.models import BaseModuleModel, Project, Run
from mq.modules.cloc import MODULE


class Cloc(BaseModuleModel):
    """..."""

    # fmt: off
    lines_blank   = IntegerField(null=True)
    lines_code    = IntegerField(null=True)
    lines_comment = IntegerField(null=True)
    scale_factor  = IntegerField(null=True)
    # fmt: on

    class Meta:
        """Define peewee meta data."""

        table_name = "cloc"
        indexes = ((("run_id", "dir", "filename"), True),)


def query_summary(run: Run):
    return (
        Cloc.select(
            fn.SUM(Cloc.lines_blank).alias("lines_blank"),
            fn.SUM(Cloc.lines_code).alias("lines_code"),
            fn.SUM(Cloc.lines_comment).alias("lines_comment"),
        )
        .where(Cloc.run_id == run.id)
        .get()
    )


def query_history(project: Project, last: int = 99999):
    run_subquery = (
        Run.select(Run.id)
        .where(
            Run.project_id == project.id,
            Run.module == MODULE,
        )
        .order_by(Run.timestamp.desc())
        .limit(99)
    )

    query = (
        Cloc.select(
            Run.timestamp.alias("timestamp"),
            fn.SUM(Cloc.lines_code).alias("total_code"),
            fn.SUM(Cloc.lines_comment).alias("total_comment"),
            fn.SUM(Cloc.lines_blank).alias("total_blank"),
        )
        .join(Run)
        .join(Project)
        .where(
            Project.id == project.id,
            Run.id.in_(run_subquery),
        )
        .group_by(Run.timestamp)
        .order_by(Run.timestamp)
        .objects()
    )

    ################################################################################################
    # Transpose (to get timestamps *across* instead of down and calculate grand totals)
    ################################################################################################
    timestamps = [result.timestamp for result in query]
    transposed = defaultdict(lambda: defaultdict(dict))
    grand_totals = defaultdict(int)
    for result in query:
        transposed["Code"][result.timestamp] = result.total_code
        transposed["Comment"][result.timestamp] = result.total_comment
        transposed["Blank"][result.timestamp] = result.total_blank

        # Calculate grand totals for each timestamp as we go
        grand_totals[result.timestamp] += result.total_code + result.total_comment + result.total_blank

    return timestamps, transposed, grand_totals
