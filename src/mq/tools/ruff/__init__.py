"""Ruff Module Configuration."""

from importlib import import_module
from typing import Callable

from mq.tools import AbstractModuleConfiguration
from mq.tools.ruff.models import Ruff

COLORS: dict = dict(positive="red", negative="green", neutral="white")


class Configuration(AbstractModuleConfiguration):
    """Configure semantics associated with using the ruff tool."""

    def __init__(self):
        """..."""
        super(Configuration, self).__init__(
            module_name="ruff",
            models=(Ruff,),
            analyses=("ruff",),
            results_required=False,  # In this case,  Ruff Scans without data ARE valid!
        )

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
        py_parse = import_module(f"mq.tools.{self.module_name}.parse")  # eg. .../<module>/parse.py
        return getattr(py_parse, "parse_json")
