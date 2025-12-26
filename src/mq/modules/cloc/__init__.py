"""Cloc Module Configuration."""

from importlib import import_module
from typing import Callable

from mq.modules import AbstractModuleConfiguration
from mq.modules.cloc.models import Cloc


MODULE = "cloc"


class Configuration(AbstractModuleConfiguration):
    """Configure semantics associated with using the cloc tool."""

    def __init__(self):
        """..."""
        super(Configuration, self).__init__(module_name=MODULE, sub_modules=("cloc",))

    def get_models(self):
        """Return the models associated with the module by sub_module."""
        return dict(cloc=Cloc)

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

    def get_parse_method(self, _) -> Callable:
        """Return the parse method to parse this Radon sub_module's JSON output."""
        py_parse = import_module(f"mq.modules.{self.module_name}.parse")  # eg. .../<module>/parse.py
        return getattr(py_parse, "parse_json")
