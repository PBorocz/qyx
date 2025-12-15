"""Report data obo running 'cloc' tool."""

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
