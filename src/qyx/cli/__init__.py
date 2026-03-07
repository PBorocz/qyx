"""CLI constants and utilities."""

import logging
import sys
from typing import Any

from rich.console import Console
from rich.table import Table

log = logging.getLogger(__name__)

################################################################################################
# Provide a common console for all CLI-based output.
################################################################################################
# If we're running to a regular terminal, Console will auto-detect & set the width,
# otherwise, use an explicit wider width (eg. stdout redirects)
cli_console = Console() if sys.stdout.isatty() else Console(width=196)


################################################################################################
def cli_table(**kwargs):
    """Provide a common Table generator that presets common formatting & styles."""
    table_kwargs: dict[str, Any] = dict(
        footer_style="bold cyan",
        header_style="bold magenta",
        show_header=True,
        title_justify="left",
        title_style="bold green",
    )
    table_kwargs.update(kwargs)  # Overlay (or replace) our defaults
    return Table(**table_kwargs)
