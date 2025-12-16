"""Report data obo running 'cloc' tool."""

from collections import defaultdict
from loguru import logger
from peewee import fn

from mq.modules.models import Project, Run
from mq.modules.cloc import MODULE
from mq.modules.cloc.models import Cloc


def _get_most_recent_project_run(project: str = ".") -> tuple[Project | None, Run | None]:
    try:
        project = Project.get(Project.source_dir_relative == project)
    except Project.DoesNotExist:
        logger.error(f"Sorry, we didn't find any data yet for project: {project}")
        return None, None

    # Get most recent Run for simple "current-state" reporting..
    if not (run := Run.get_most_recent(project, MODULE)):
        logger.error("Sorry, we haven't performed a CLOC measurement yet for this project.")
        return None, None
    return project, run


def render_summary() -> None:
    project, run = _get_most_recent_project_run()
    logger.info(f"{project=} {run=}")
    results = Cloc.select(
        fn.SUM(Cloc.lines_blank).alias("lines_blank"),
        fn.SUM(Cloc.lines_code).alias("lines_code"),
        fn.SUM(Cloc.lines_comment).alias("lines_comment"),
    ).get()
    return results


def render_history(project: Project, last: int = 99999):
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

    # START HERE!
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
