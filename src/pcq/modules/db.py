"""..."""

from argman.argman import _ArgResult
from peewee import fn, SqliteDatabase

from pcq.models import Project, Run
from pcq.modules import MODULES


def flush(args: _ArgResult, db: SqliteDatabase) -> None:
    if args.flush.module:
        assert args.flush.module in MODULES
        # Delete all the data associated with the specified module.
        for project in Project.select():
            for run in Run.select().where(Run.module == args.flush.module):
                for model in MODULES[args.flush.module]:
                    model.delete().where(model.run_id == run.id).execute()
            Run.delete().where(Run.module == args.flush.module).execute()
    else:
        for name, modules in MODULES.items():
            for model in modules:
                model.delete().execute()
        Run.delete().execute()
        Project.delete().execute()


def purge(args: _ArgResult, db: SqliteDatabase) -> None:
    """Purge/delete all data associated with "old" runs, ie, lose history but keep most recent!"""
    # First, gather the most recent run for each module/sub-module we've got data for..
    runs_to_keep = Run.select(
        Run.id,
        fn.MAX(Run.timestamp).alias(
            "max_timestamp",
        ),
    ).group_by(
        Run.project_id,
        Run.module,
        Run.sub_module,
    )
    if args.purge.debug:
        print(f"{runs_to_keep=}")

    # Now, we can delete data associated with runs that AREN'T the most recent:
    for run in Run.select():
        if run.id not in [run.id for run in runs_to_keep]:
            for model in MODULES[run.module]:
                num_deleted = model.delete().where(model.run_id == run.id).execute()
                if num_deleted:
                    print(
                        f"Deleted {num_deleted} rows from {run.module}/{run.sub_module} obo {run.id} ({run.timestamp})"
                    )
            Run.delete().where(Run.id == run.id).execute()
