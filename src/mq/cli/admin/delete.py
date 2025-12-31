"""..."""

import logging
from argparse import Namespace
from typing import Callable

from mq.cli import cli_console
from mq.cli.admin import do_it
from mq.tools.base import Project, Request, Scan

log = logging.getLogger(__name__)


def delete(args: Namespace) -> None:
    """Delete the specified Project, Request or Scan."""
    # Did we even *get* an argument to work from?
    if not args.delete_target:
        raise RuntimeError("Sorry, we need to have a particular project, request or scan specified!")

    # Is it in the right format?
    if ":" not in args.delete_target:
        raise RuntimeError("Sorry, format needs to either 'p:<id>', 'r:<id>' or 's:<id>'!")

    entity, id_ = args.delete_target.lower().split(":")
    if entity not in ("p", "r", "s"):
        raise RuntimeError("Sorry, format needs to either 'p:<id>', 'r:<id>' or 's:<id>'!")

    try:
        _ = int(id_)
    except TypeError:
        raise RuntimeError("Sorry, 'id' needs to be numeric in 'p:<id>', 'r:<id>' or 's:<id>'!")

    # Do it after potential confirmation
    match entity:
        case "p":
            _confirm_and_execute(
                args,
                f"Delete [red]all[/red] data for Project id {id_}?",
                lambda: Project.delete().where(Project.id == int(id_)).execute(),
            )
        case "r":
            _confirm_and_execute(
                args,
                f"Delete [red]all[/red] data for Request id {id_}?",
                lambda: Request.delete().where(Request.id == int(id_)).execute(),
            )
        case "s":
            _confirm_and_execute(
                args,
                f"Delete [red]all[/red] data for Scan id {id_}?",
                lambda: Scan.delete().where(Scan.id == int(id_)).execute(),
            )


def _confirm_and_execute(args, prompt: str, delete_lambda: Callable) -> None:
    """Helper to reduce repetition."""
    if do_it(args, prompt):
        delete_lambda()
        cli_console.print("[green]✓ Data cleared successfully.[/green]")
    else:
        cli_console.print("[blue]Ok, nothing done.[/blue]")
