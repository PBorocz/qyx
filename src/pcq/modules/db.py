"""..."""

from argman.argman import _ArgResult
from peewee import SqliteDatabase

from pcq.models import Run
from pcq.modules.ruff_check import RuffCheck


def flush(args: _ArgResult, db: SqliteDatabase) -> None:
    if args.flush.module:
        for run in Run.select().where(Run.run_module == args.flush.module):
            RuffCheck.delete().where(RuffCheck.run_id == run.id).execute()
        Run.delete().where(Run.run_module == args.flush.module).execute()
    else:
        RuffCheck.delete().execute()
        Run.delete().execute()
