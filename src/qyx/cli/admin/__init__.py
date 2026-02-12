"""Admin command common methods."""

from argparse import Namespace

from rich.prompt import Confirm

from qyx.cli import cli_console


def do_it(args: Namespace, message: str) -> bool:
    _do_it: bool = args.no_confirm
    if not _do_it:
        cli_console.print(f"[bold red]⚠️ WARNING: {message}[/bold red]")
        _do_it = Confirm.ask("[yellow]Are you sure you want to continue?[/yellow]", default=False)
    return _do_it
