"""..."""

import logging
from argparse import Namespace
from pathlib import Path

from platformdirs import user_data_dir

from mq.cli import cli_console
from mq.cli.admin import do_it
from mq.tools.base import Project, Request, Scan

log = logging.getLogger(__name__)


def clear(args: Namespace) -> None:
    raise NotImplementedError("!")

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
        if not (project := Project.find_from_args(args)):
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
