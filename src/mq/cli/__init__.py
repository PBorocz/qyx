"""CLI constants and utilities."""

import importlib
import logging
import sys
from typing import Callable

from rich.console import Console
from rich.table import Table

log = logging.getLogger(__name__)

################################################################################################
# Provide a common console for all CLI-based output.
################################################################################################
# If we're running to a regular terminal, Console will auto-detect & set the width,
# otherwise, use an explicit wider width (eg. stdout redirects)
kwargs = dict() if sys.stdout.isatty() else dict(width=196)
cli_console = Console(**kwargs)


################################################################################################
def cli_table(**kwargs):
    """Provide a common Table generator that presets common formatting & styles."""
    table_kwargs = dict(
        footer_style="bold cyan",
        header_style="bold magenta",
        show_header=True,
        title_justify="left",
        title_style="bold green",
    )
    table_kwargs.update(kwargs)  # Overlay (or replace) our defaults
    return Table(**table_kwargs)


################################################################################################
def get_method(module_dir: str, py_filename: str, method: str) -> tuple[Callable | None, str | None]:
    module_path = f"mq.modules.{module_dir}.{py_filename}"  # Construct the path to the specific .py file
    log.debug(f"Using {module_path=}")
    try:
        module = importlib.import_module(module_path)  # ...and import it.
    except ImportError as e:
        return None, f"Could not import {module_path}: {e}"

    try:
        return getattr(module, method), None  # Return the method from the module
    except AttributeError as e:
        return None, f"Method {method} not found in {module_path}: {e}"
