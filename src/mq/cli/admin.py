"""..."""

import logging
from argparse import Namespace
from pathlib import Path

from peewee import fn
from platformdirs import user_data_dir
from rich.prompt import Confirm

from mq.cli import cli_console
from mq.modules import AbstractModuleConfiguration
from mq.modules.base import Project, Request, Scan

log = logging.getLogger(__name__)


def housekeeping(args: Namespace) -> None:
    """Clean out extraneous Scans that don't have data and Projects that don't have Scans."""
    _delete_extraneous_scans(args)
    _delete_extraneous_requests(args)
    _delete_extraneous_projects(args)


def _delete_extraneous_scans(args: Namespace) -> None:
    """Delete orphaned Sequests, ie. that don't have results associated with 'em."""

    def __clean_scans(module_name: str, module_config: AbstractModuleConfiguration) -> None:
        # log.debug(f"Cleanup {module_name=}")
        # First, get all the scan's id's used by models in this module:
        model_scan_ids = set()
        for tool, model in module_config.get_models().items():
            result_scan_ids = [row.scan_id for row in model.select(model.scan).distinct()]
            model_scan_ids.update(result_scan_ids)
            # log.debug(f"-- Results '{model.__name__:9s}' has {len(result_scan_ids):2d} scan(s) with data.")

        # log.debug(f"- {module_name:6s} {len(model_scan_ids)=:2d} {sorted(model_scan_ids)}")

        # Secondly, gather all the scan's currently stored for this module
        scan_ids = {scan.id for scan in Scan.select().where(Scan.module == module_name)}
        # log.debug(f"- {module_name:6s} has {len(scan_ids):2d} scans on it's behalf {sorted(scan_ids)}")

        # Find any "extraneous" ones by simple set subtract (!) and delete 'em.
        scan_ids_to_delete = scan_ids - model_scan_ids
        if scan_ids_to_delete:
            # num = Scan.delete().where(Scan.id.in_(scan_ids_to_delete)).execute()
            num = 0
            msg = f"- Cleaned up {num} Scan(s) that weren't referenced."
        else:
            msg = "Nothing done, all Scans have Results associated with them."
        log.debug(msg)

    for module_name, module_config in args.modules.items():
        if not module_config.results_required:
            # log.debug(f"(skipping module: {module_name} from housekeeping as data is NOT required)")
            continue
        __clean_scans(module_name, module_config)


def _delete_extraneous_requests(args: Namespace) -> None:
    """Delete orphaned Requests, ie. that don't have scans associated with 'em."""
    num = Request.delete().where(Request.id.not_in(Scan.select(Scan.request).distinct())).execute()
    if num:
        log.debug(f"Cleaned up {num} Requests that had no Scans defined on their behalf.")
    else:
        log.debug("Nothing done, all Requests have Scans associated with them.")


def _delete_extraneous_projects(args: Namespace):
    """Delete orphaned Projects, ie. that don't have requests associated with 'em."""
    num = Project.delete().where(Project.id.not_in(Request.select(Request.project).distinct())).execute()
    if num:
        log.debug(f"Cleaned up {num} Projects that had no Requests defined on their behalf.")
    else:
        log.debug("Nothing done, all Projects have Requests associated with them.")


def clear(args: Namespace) -> None:
    def _delete_database():
        db_path = Path(user_data_dir("mq")) / "mq.sqlite3"
        db_path.unlink(missing_ok=True)

    def _confirm_and_execute(prompt: str, delete_lambda) -> None:
        """Helper to reduce repetition."""
        if do_it(args, prompt):
            delete_lambda()
            cli_console.print("[green]✓ Data cleared successfully.[/green]")
        else:
            cli_console.print("[blue]Ok, nothing done.[/blue]")

    if args.project:
        if not (project := Project.get_by_identifier(args.project)):
            cli_console.print("[red]Sorry, unable to find project: {args.project}[/red]")
            return

    ################################################################################################
    if args.project and args.module:
        # Delete all the data associated with the specified module for the specified project:
        _confirm_and_execute(
            f"Delete all data for project: '{project.name}' and module: '{args.module}'?",
            lambda: Scan.delete()
            .where(
                Scan.request.in_(Request.select().where(Request.project == project)),
                Scan.module == args.module,
            )
            .execute(),
        )
        return

    ################################################################################################
    elif args.project and not args.module:
        _confirm_and_execute(
            f"Delete all data for project: '{project.name}'?",
            lambda: Request.delete().where(Request.project == project).execute(),
        )
        return

    ################################################################################################
    elif not args.project and args.module:
        _confirm_and_execute(
            f"Delete all data for module: '{args.module}'?",
            lambda: Scan.delete().where(Scan.module == args.module).execute(),
        )
        return

    ################################################################################################
    else:
        # Delete everything
        _confirm_and_execute("Delete ALL data!!?", _delete_database)


def do_it(args: Namespace, message: str) -> bool:
    _do_it: bool = args.no_confirm
    if not _do_it:
        cli_console.print(f"[bold red]⚠️ WARNING: {message}[/bold red]")
        _do_it = Confirm.ask("[yellow]Are you sure you want to continue?[/yellow]", default=False)
    return _do_it


def trim(args: Namespace) -> None:
    """Clear/delete/*TRIM* all data associated with "old" scan, ie, lose history but keep most recent!"""
    # TODO: Implement ability to trim by either Project OR Module (or both!)
    if do_it(args, "This will delete 'older' data! (leaving the most recent Scan for each module & project)"):
        count = _trim(args)
        if count:
            msg = f"[green]✓ {count:,} old scans cleared successfully.[/green]"
        else:
            msg = "[green]✓ No old scans found.[/green]"

    else:
        msg = "[blue]Ok, nothing done.[/blue]"

    cli_console.print(msg)


def _trim(args: Namespace) -> int:
    """Trim scans that are NOT the most recent for each project, module and sub-module."""
    # Get the *most recent* scan for each combination of project, module and sub-module.
    scans_to_keep = (
        Scan.select(
            Scan.id,
            Scan.request,
            Project.name.alias("project_name"),
            Scan.module,
            Scan.sub_module,
            fn.MAX(Scan.timestamp).alias("max_timestamp"),
        )
        .join(Request)
        .join(Project)
        .group_by(Project, Scan.module, Scan.sub_module)
        .objects()
    )

    # log.debug("The following scans are the most current:")
    # for scan in scans_to_keep:
    #     log.debug(f"{scan.id=} {scan.project_name} {scan.request.id=} {scan.module=} {scan.sub_module=}")

    # Delete scans that *ARE NOT* the most recent:
    count = 0
    for scan in Scan.select():
        if scan.id not in [scan.id for scan in scans_to_keep]:
            if args.module and args.module != scan.module:
                continue
            Scan.delete().where(Scan.id == scan.id).execute()
            count += 1
    return count
