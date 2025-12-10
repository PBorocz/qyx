"""..."""

from argparse import Namespace
from loguru import logger
from peewee import fn, SqliteDatabase
from rich.console import Console
from rich.table import Table

from pcq.models import Project, Run
from pcq.modules.ruff import MODULE
from pcq.modules.ruff.models import Ruff
from pcq.utilities import remove_common_prefixes


def report(args: Namespace, db: SqliteDatabase) -> None:
    project = Project.get(source_dir=args.project)
    run = Run.select().order_by(Run.timestamp.desc()).where(Run.project_id == project.id, Run.module == MODULE).first()
    if not run:
        logger.info("No runs yet.")
        return
    if args.verbosity == 0:
        results = (
            Ruff.select(Ruff.rule_code, Ruff.message, fn.COUNT(Ruff.id).alias("count"))
            .where(Ruff.run_id == run)
            .group_by(Ruff.rule_code)
            .order_by(fn.COUNT(Ruff.id).desc())
        )
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Rule")
        table.add_column("Count", justify="center")
        table.add_column("Message")
        for result in results:
            table.add_row(result.rule_code, str(result.count), result.message)
        Console().print(table)

    elif args.verbosity == 1:
        logger.info(f"{run.timestamp_local} : Following ruff checks encountered:")
        rows = Ruff.select().where(Ruff.run_id == run).order_by(Ruff.filename, Ruff.rule_code)
        foobar = 1
        rows = remove_common_prefixes(rows)
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Rule")
        table.add_column("File (line)")
        table.add_column("Message")
        for row in rows:
            table.add_row(row.rule_code, f"{row.filename} [{row.line}] ", row.message)
        Console().print(table)
