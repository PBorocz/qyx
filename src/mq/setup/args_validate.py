"""."""

import subprocess
from argparse import Namespace
from pathlib import Path
from typing import Optional

from rich import print as rprint

from mq.tools import split_arg_tool_analysis
from mq.utils import is_git_url


def validate_args(args: Namespace) -> bool:
    """Validate arguments now that we've got everything setup."""
    # Validate command-specific arguments:
    issues = []
    match args.command.lower():
        case "ingest":
            issues.extend(_validate_ingest(args))
        case "report":
            issues.extend(_validate_report(args))

    # Irrespective of the command, if a tool:analysis was specifed, validate it:
    if "analysis" in args:
        issues.extend(_validate_tool_analysis(args))

    # Did we find anything untowards?
    if issues:
        for issue in issues:
            rprint(f"• {issue}")
        return False
    return True


def _validate_ingest(args: Namespace) -> list[str]:
    return_ = []
    if not args.name:
        return_.append("[red]Sorry! [bold]-n/--name[/bold] is required to perform an ingest!")

    if args.path:
        if is_git_url(args.path):
            # Putative remote path, is it valid?
            is_valid, error = _validate_git_remote(args.path)
            if not is_valid:
                return_.append(f"[red]Error: {error}[/red]")
        else:
            # Putative local path (ie. not pointing to a git repo), is it valid?
            # Does it exist?
            if not Path(args.path).exists():
                return_.append(f"[red]Path '{args.path}' [bold]doesn't exist[/bold]")

            # Is is a directory?
            elif not Path(args.path).is_dir():
                return_.append(f"[red]Path '{args.path}' exists but is [bold]not[/bold] a directory")

            # Is it a "valid" directory (or sub-directory) of a git project?
            elif not __find_git_root(Path(args.path)):
                return_.append(
                    f"[red]Path '{args.path}' is [bold]not[/bold] a git repository[/red] "
                    "(specify a path that is .git project root or sub-directory)",
                )
    else:
        if not args.stdin:
            return_.append(
                "[red]Sorry! you need to either specify [bold]-p/--path[/bold] "
                "OR provide data from [bold]--stdin[/bold] to perform an ingest.",
            )

    return return_


def _validate_report(args: Namespace) -> list[str]:
    if not args.name:
        return ["[red]Sorry! [bold]-n/--name[/bold] is required to report results."]
    return []


def _validate_tool_analysis(args: Namespace) -> list[str]:
    tool, analysis, sub = split_arg_tool_analysis(args.tool_analysis)
    if tool not in args.tools:
        s_names = ", ".join(args.tools.keys())
        return (
            f"[red]Sorry! analysis: [bold]{args.tool_analysis}[/bold] is not valid, "
            f"tool must be one of:[/red] [blue]{s_names}[/blue]",
        )


def __find_git_root(dir: Path) -> Path | None:
    """Find the git root, walking up if needed, returning None if we can't find one."""
    current = dir.resolve()

    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent

    return None


def _validate_git_remote(url: str, timeout: int = 10) -> tuple[bool, Optional[str]]:
    """Validate git URL by checking remote. Returns (is_valid, error_message)."""
    try:
        result = subprocess.run(
            ["git", "ls-remote", "--exit-code", "--heads", url],
            capture_output=True,
            timeout=timeout,
            text=True,
        )

        if result.returncode == 0:
            return True, None
        elif result.returncode == 128:
            # Git error (invalid URL, auth failure, etc.)
            return False, result.stderr.strip()
        else:
            return False, "Repository not found or not accessible"

    except subprocess.TimeoutExpired:
        return False, f"Timeout after {timeout}s - repository unreachable"

    except FileNotFoundError:
        return False, "git command not found"

    except Exception as e:
        return False, str(e)
