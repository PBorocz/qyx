"""Ruff Module Configuration."""

from importlib import import_module
from typing import Callable

from mq.tools.base import AbstractModuleConfiguration
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
        """Return the command sent to subprocess to directly perform a Ruff operation."""
        return [
            "ruff",
            "check",
            "--exit-zero",
            "--output-format=json",
            project_path,
        ]

    def get_ingest_method(self, _) -> Callable:
        """Return the ingest method to parse and save this Ruff JSON output."""
        py_ingest = import_module(f"mq.tools.{self.module_name}.ingest")  # eg. .../<module>/ingest.py
        return getattr(py_ingest, "ingest")
