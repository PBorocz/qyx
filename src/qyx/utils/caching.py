"""A simple decorator over query methods that keys by project, scan or both."""

import inspect
import os
from functools import wraps
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

# Module-level shared cache
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

        # Build cache key from project.id and/or scan.id
        key_parts = []

        project = bound_args.arguments.get("project")
        if project is not None:
            key_parts.append(("project", project.id))

        scan = bound_args.arguments.get("scan")
        if scan is not None:
            key_parts.append(("scan", scan.id))

        # Create immutable cache key
        cache_key = (func.__name__, tuple(key_parts))

        # Return cached result if available
        if cache_key in _QUERY_CACHE:
            return _QUERY_CACHE[cache_key]

        # Execute function and cache result
        result = func(*args, **kwargs)
        _QUERY_CACHE[cache_key] = result
        return result

    return wrapper  # type: ignore


def query_cache_info() -> dict[str, Any]:
    """Get information about the entire query cache."""
    # Group by function name
    by_function: dict[str, int] = {}
    for key in _QUERY_CACHE.keys():
        func_name = key[0]
        by_function[func_name] = by_function.get(func_name, 0) + 1

    return {
        "total_size": len(_QUERY_CACHE),
        "by_function": by_function,
        "all_keys": list(_QUERY_CACHE.keys()),
    }
