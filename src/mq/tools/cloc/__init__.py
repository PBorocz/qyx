"""Cloc Module Configuration."""

from mq.constants import ReportLevel as Rl
from mq.tools.base import ToolConfig
from mq.tools.cloc.models import Cloc


class Configuration(ToolConfig):
    """Configure semantics associated with using the cloc tool."""

    def __init__(self):
        """..."""
        # fmt: off
        cli = dict(
            cloc = (Rl.SUMMARY, Rl.DIRECTORY, Rl.FILE, Rl.DERIVED, Rl.HISTORY),
        )
        web = dict(
            cloc = (Rl.SUMMARY, Rl.DIRECTORY, Rl.FILE, Rl.DERIVED, Rl.HISTORY),
        )
        # fmt: on

        super(Configuration, self).__init__(
            module_name="cloc",
            models=dict(cloc=Cloc),
            reports=dict(cli=cli, web=web),
        )

    def get_ingest_command(self, relative: str = None, absolute: str = None, analysis: str = None) -> list[str]:
        """Return the command sent to subprocess to directly perform a CLOC operation."""
        return [
            "cloc",
            "--by-file",
            "--include-lang=Python",
            "--json",
            "--vcs=git",
            absolute,
        ]
