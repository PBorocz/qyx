"""Cloc Module Configuration."""

from importlib import import_module
from typing import Callable

from mq.tools import AbstractModuleConfiguration
from mq.tools.cloc.models import Cloc


class Configuration(AbstractModuleConfiguration):
    """Configure semantics associated with using the cloc tool."""

    def __init__(self):
        """..."""
        super(Configuration, self).__init__(
            module_name="cloc",
            models=(Cloc,),
            analyses=("cloc",),
        )

    def get_ingest_command(self, project_path: str, _) -> list[str]:
        """Return the command sent to subprocess to directly perform a CLOC operation."""
        return [
            "cloc",
            "--include-lang=Python",
            "--by-file",
            "--json",
            "--exclude-dir=.venv",
            project_path,
        ]

    def get_ingest_method(self, _) -> Callable:
        """Return the ingest method to parse and save Cloc JSON output."""
        py_ingest = import_module(f"mq.tools.{self.module_name}.ingest")  # eg. .../<module>/ingest.py
        return getattr(py_ingest, "ingest")
