"""A simple decorator over query methods that keys by project, scan or both."""
# Disclaimer: I didn't have the patience for this so Claude was 90% responsible for this module!

import inspect
import os
import sys
from functools import wraps
from typing import Any, Callable, TypeVar

from rich import print as rprint
from rich.table import Table
from rich.panel import Panel
from rich.console import Console

F = TypeVar("F", bound=Callable[..., Any])

# Module-level shared cache: cache_key -> query result
_QUERY_CACHE: dict[tuple, Any] = {}


def query_cache(func: F) -> F:
    """Cache decorator that uses project.id and scan.id as cache keys (ignoring other args)."""

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        # Check if caching is enabled before continuing (default is *to* cache).
        if os.getenv("QYX_QUERY_CACHE_DISABLED"):
            return func(*args, **kwargs)

        # Bind all arguments to their parameter names
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()

        # Build cache key from project.id *AND/OR* scan.id
        key_parts = []

        project = bound_args.arguments.get("project")
        if project is not None:
            key_parts.append(("project", project.id))

        scan = bound_args.arguments.get("scan")
        if scan is not None:
            key_parts.append(("scan", scan.id))

        # Create immutable cache key
        # Note: critical that we include the module as well since we
        # re-use query method names across modules! (eg. query_0, query_1, etc.)
        cache_key = (func.__module__, func.__qualname__, tuple(key_parts))

        # Return cached result if available
        if cache_key in _QUERY_CACHE:
            return _QUERY_CACHE[cache_key]

        # Execute function and cache result
        result = func(*args, **kwargs)
        _QUERY_CACHE[cache_key] = result
        return result

    return wrapper  # type: ignore


################################################################################################
def cache_info(args_unused) -> None:
    """Display information about the current contents of the query cache."""
    query_summary = _get_cache_info()
    console = Console()

    # Create summary panel
    total_size = query_summary["total_size_bytes"]
    summary = (
        f"[bold cyan]Total Cached Entries :[/bold cyan] {query_summary['total_size']}\n"
        f"[bold cyan]Total Memory Size    :[/bold cyan] {_format_bytes(total_size)}"
    )
    console.print(Panel(summary, title="Query Cache Status", border_style="cyan"))

    if query_summary["total_size"] == 0:
        rprint("[yellow]Cache is empty.[/yellow]")
        return

    # Create table for cache breakdown
    table = Table(title="Cache Breakdown by Function", show_header=True, header_style="bold magenta")
    table.add_column("Module", style="cyan", no_wrap=True)
    table.add_column("Function", style="green")
    table.add_column("Entries", justify="right", style="yellow")
    table.add_column("Size", justify="right", style="blue")
    for (module, func_name), info in sorted(query_summary["by_function"].items()):
        table.add_row(module, func_name, str(info["count"]), _format_bytes(info["size"]))

    console.print(table)
    console.print()


def _get_cache_info() -> dict[str, Any]:
    by_function: dict[tuple[str, str], dict[str, Any]] = {}
    total_size_bytes = 0
    for key, value in _QUERY_CACHE.items():
        func_key = key[:2]  # (module, function)

        if func_key not in by_function:
            by_function[func_key] = {"count": 0, "size": 0}

        size = sys.getsizeof(value)
        by_function[func_key]["count"] += 1
        by_function[func_key]["size"] += size
        total_size_bytes += size

    return {
        "total_size": len(_QUERY_CACHE),
        "total_size_bytes": total_size_bytes,
        "by_function": by_function,
    }


def _format_bytes(bytes: int) -> str:
    """Format bytes into human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} TB"
