"""..."""

import logging
from argparse import Namespace
from pathlib import Path

from peewee import fn
from platformdirs import user_data_dir
from rich.prompt import Confirm

from mq.cli import cli_console
from mq.modules.base import Project, Run
from mq.modules import models_for_module, MODULES_AND_MODELS

log = logging.getLogger(__name__)


def housekeeping(args: Namespace) -> None:
    """Clean out extraneous Runs that don't have data and Projects that don't have Runs."""

    def __cleanup(module_name: str, module_info: dict) -> None:
        # First, get all the run's id's used by models in this module:
        model_run_ids = set()
        models = module_info["models"]
        for model in models:
            model_run_ids.update([row.run_id for row in model.select(model.run).distinct()])
        log.debug(f"- {module_name:6s} {len(models)=:1d} {len(model_run_ids)=:2d} : {sorted(model_run_ids)}")

        # Secondly, gather all the run's currently stored for this module
        run_ids = {run.id for run in Run.select().where(Run.module == module_name)}
        log.debug(f"- {'Run':6s} {len(run_ids)=:2d} : {sorted(run_ids)}")

        # Find any "extraneous" ones by simple set subtract (!) and delete 'em.
        run_ids_to_delete = run_ids - model_run_ids
        if run_ids_to_delete:
            num = Run.delete().where(Run.id.in_(run_ids_to_delete)).execute()
            msg = f"- Cleaned up {num} Run(s) that weren't referenced."
        else:
            msg = "- No runs needed to be cleaned up."
        log.debug(msg)

    def _delete_unused_runs(args: Namespace):
        """Delete orphaned Run rows on behalf of modules that REQUIRE data to be valid."""
        for module_name, module_info in MODULES_AND_MODELS.items():
            module = module_info["module"]
            log.debug(f"Considering {module_name=}")
            if not module.RESULTS_REQUIRED:
                log.debug(f"(skipping module: {module_name} from housekeeping as data is NOT required)")
                continue

            __cleanup(module_name, module_info)

    def _delete_unused_projects(args: Namespace):
        """Delete orphaned Project rows."""
        num = Project.delete().where(Project.id.not_in(Run.select(Run.project).distinct())).execute()
        if num:
            log.debug(f"Cleaned up {num} Projects that had no Runs defined.")

    _delete_unused_runs(args)
    _delete_unused_projects(args)


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
            cli_console.print("[green]✓ Data cleared successfully.[/green]")
        else:
            cli_console.print("[blue]Ok, nothing done.[/blue]")


def trim(args: Namespace) -> None:
    """Clear/delete all data associated with "old" runs, ie, lose history but keep most recent!"""
    should_trim = args.no_confirm
    if not should_trim:
        cli_console.print("[bold red]⚠️  WARNING: This will delete older data![/bold red]")
        should_trim = Confirm.ask("[yellow]Ok to continue?[/yellow]", default=False)

    if should_trim:
        _trim(args)
        cli_console.print("[green]✓ Older data cleared successfully.[/green]")
    else:
        cli_console.print("[blue]Ok, nothing done.[/blue]")


def _trim(args: Namespace) -> None:
    """Trim runs that are NOT the most recent for each project, module and sub-module."""
    # Get the *most recent* run..
    runs_to_keep = Run.select(
        Run.id,
        fn.MAX(Run.timestamp).alias("max_timestamp"),
    ).group_by(
        Run.project,
        Run.module,
        Run.sub_module,
    )

    # Delete runs that *ARE NOT* the most recent:
    # (recognising that it might be for just a single module)
    for run in Run.select():
        if run.id not in [run.id for run in runs_to_keep]:
            if args.module and args.module != run.module:
                continue
            Run.delete().where(Run.id == run.id).execute()
