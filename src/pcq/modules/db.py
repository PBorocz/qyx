"""..."""

from argman.argman import _ArgResult
from peewee import SqliteDatabase

from pcq.models import Project, Run
from pcq.modules.cloc import Cloc
from pcq.modules.ruff import Ruff


def flush(args: _ArgResult, db: SqliteDatabase) -> None:
    if args.flush.module:
        for project in Project.select():
            for run in Run.select().where(Run.module == args.flush.module):
                Ruff.delete().where(Ruff.run_id == run.id).execute()
                Cloc.delete().where(Ruff.run_id == run.id).execute()
            Run.delete().where(Run.module == args.flush.module).execute()
    else:
        Cloc.delete().execute()
        Ruff.delete().execute()
        Run.delete().execute()
        Project.delete().execute()
