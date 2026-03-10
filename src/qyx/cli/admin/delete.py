"""..."""

import logging
from argparse import Namespace
from typing import Callable

from qyx.cli import cli_console
from qyx.cli.admin import do_it
from qyx.constants import BaseModel
from qyx.tools._models_ import Project, Request, Scan

log = logging.getLogger(__name__)


def delete(args: Namespace) -> None:
    """Delete the specified Project, Request or Scan."""
    # Did we even *get* an argument to work from?
    if not args.delete_target:
        raise RuntimeError("Sorry, we need to have a particular project, request or scan")

    # Is it in the right format?
    if ":" not in args.delete_target:
        raise RuntimeError("Sorry, format needs to either 'project:<id>', 'request:<id>' or 'scan:<id>'!")

    raw_entity, id_ = args.delete_target.lower().split(":")
    try:
        entity = BaseModel(raw_entity)
    except ValueError:
        raise RuntimeError("Sorry, invalid format, needs to be any of 'project:<id>', 'request:<id>' or 'scan:<id>'!")

    try:
        _ = int(id_)
    except TypeError:
        raise RuntimeError("Sorry, 'id' needs to be numeric!")

    # Do it after potential confirmation
    match entity:
        case BaseModel.PROJECT:
            _confirm_and_execute(
                args,
                f"Delete [red]all[/red] data for Project id {id_}?",
                lambda: Project.delete().where(Project.id == int(id_)).execute(),
            )
        case BaseModel.REQUEST:
            _confirm_and_execute(
                args,
                f"Delete [red]all[/red] data for Request id {id_}?",
                lambda: Request.delete().where(Request.id == int(id_)).execute(),
            )
        case BaseModel.SCAN:
            _confirm_and_execute(
                args,
                f"Delete [red]all[/red] data for Scan id {id_}?",
                lambda: Scan.delete().where(Scan.id == int(id_)).execute(),
            )


def _confirm_and_execute(args: Namespace, prompt: str, delete_lambda: Callable) -> None:
    """Helper to reduce repetition."""
    if do_it(args, prompt):
        delete_lambda()
        cli_console.print("[green]✓ Data cleared successfully.[/green]")
    else:
        cli_console.print("[blue]Ok, nothing done.[/blue]")
