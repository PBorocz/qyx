"""Ruff Module Configuration."""

from importlib import import_module
from typing import Callable

from mq.modules import AbstractModuleConfiguration
from mq.modules.ruff.models import Ruff

MODULE: str = "ruff"
COLORS = dict(positive="red", negative="green", neutral="white")


class Configuration(AbstractModuleConfiguration):
    """Configure semantics associated with using the ruff tool."""

    def __init__(self):
        """..."""
        super(Configuration, self).__init__(
            module_name=MODULE,
            sub_modules=("ruff",),
            results_required=False,  # In this case,  Ruff Scans without data ARE valid!
        )

    def get_models(self):
        """Return the models associated with the module by sub_module."""
        return dict(ruff=Ruff)

    def get_ingest_command(self, project_path: str, _) -> list[str]:
        """Return the command sent to subprocess to directly perform a CLOC operation."""
        return [
            "ruff",
            "check",
            "--exit-zero",
            "--output-format=json",
            project_path,
        ]

    def get_parse_method(self, _) -> Callable:
        """Return the parse method to parse this Radon sub_module's JSON output."""
        py_parse = import_module(f"mq.modules.{self.module_name}.parse")  # eg. .../<module>/parse.py
        return getattr(py_parse, "parse_json")
