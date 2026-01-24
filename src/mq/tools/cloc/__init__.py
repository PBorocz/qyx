"""Cloc Module Configuration."""

from mq.tools.base import AbstractToolConfiguration
from mq.tools.cloc.models import Cloc


class Configuration(AbstractToolConfiguration):
    """Configure semantics associated with using the cloc tool."""

    def __init__(self):
        """..."""
        super(Configuration, self).__init__(
            module_name="cloc",
            models=dict(cloc=Cloc),
        )

    def get_ingest_command(self, relative: str = None, absolute: str = None, analysis: str = None) -> list[str]:
        """Return the command sent to subprocess to directly perform a CLOC operation."""
        return [
            "cloc",
            "--include-lang=Python",
            "--by-file",
            "--json",
            "--exclude-dir=.venv",
            absolute,
        ]
