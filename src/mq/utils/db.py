"""..."""

from argparse import Namespace
from pathlib import Path

from loguru import logger
from peewee import fn
from platformdirs import user_data_dir
from rich.prompt import Confirm

from mq.cli import cli_console
from mq.modules.models import Project, Run
from mq.modules import models_for_module, MODULE_MODELS


def housekeeping(args: Namespace) -> None:
    """Clean out extraneous Runs that don't have data and Projects that don't have Runs."""

    def _unused_runs(args: Namespace):
        """Delete orphaned Run rows."""
        # Gather all the current run id's
        run_ids_used = set()
        for model in MODULE_MODELS:
            models_run_ids = model.select(model.run).distinct()
            run_ids_used.update([row.run_id for row in models_run_ids])

        # Delete Runs that aren't currently used
        if run_ids_used:
            logger.debug(f"We have {len(run_ids_used)} active Runs currently.")
            num = Run.delete().where(Run.id.not_in(run_ids_used)).execute()
            if num:
                logger.debug(f"Cleaned up {num} Run(s) that weren't referenced.")

    def _unused_projects(args: Namespace):
        """Delete orphaned Project rows."""
        num = Project.delete().where(Project.id.not_in(Run.select(Run.project).distinct())).execute()
        if num:
            logger.debug(f"Cleaned up {num} Projects that had no Runs defined.")

    _unused_runs(args)
    _unused_projects(args)


def clear(args: Namespace) -> None:
    def __delete_database():
        db_path = Path(user_data_dir("mq")) / "mq.sqlite3"
        db_path.unlink(missing_ok=True)

    if args.module:
        # Delete all the data associated with the specified module.
        for project in Project.select():
            for run in Run.select().where(Run.module == args.module):
                for model in models_for_module(args.module):
                    model.delete().where(model.run == run.id).execute()
            Run.delete().where(Run.module == args.module).execute()
    else:
        # In this case, we can simply nuke the entire db file (this is
        # useful if we want to apply an updated schema *AND* don't care
        # about losing existing data)
        should_delete = args.no_confirm
        if not should_delete:
            cli_console.print("[bold red]⚠️  WARNING: This will delete ALL data![/bold red]")
            should_delete = Confirm.ask("[yellow]Are you sure you want to continue?[/yellow]", default=False)

        if should_delete:
            __delete_database()
            cli_console.print("[green]✓ Data cleared successfully[/green]")
        else:
            cli_console.print("[blue]Ok, nothing done[/blue]")


def trim(args: Namespace) -> None:
    """Clear/delete all data associated with "old" runs, ie, lose history but keep most recent!"""
    # First, gather the most recent run for each module/sub-module we've got data for..
    runs_to_keep = Run.select(
        Run.id,
        fn.MAX(Run.timestamp).alias(
            "max_timestamp",
        ),
    ).group_by(
        Run.project,
        Run.module,
        Run.sub_module,
    )

    # Now, we can delete data associated with runs that AREN'T the most recent:
    for run in Run.select():
        if run.id not in [run.id for run in runs_to_keep]:
            if args.module and args.module != run.module:
                continue

            num_deleted = 0
            for model in models_for_module(run.module):
                num_deleted += model.delete().where(model.run == run.id).execute()
            if num_deleted:
                logger.debug(f"Deleted {num_deleted:3d} rows {run.module:5s} from {run.timestamp}")

            # Cleanup the run itself as well.
            Run.delete().where(Run.id == run.id).execute()
