"""FixMe ToDo Module Configuration."""

from importlib import import_module
from typing import Callable

from mq.tools.base import AbstractModuleConfiguration
from mq.tools.fxtd.models import Fxtd

COLORS: dict = dict(positive="red", negative="green", neutral="white")


class Configuration(AbstractModuleConfiguration):
    """Configure semantics associated with using the tool."""

    def __init__(self):
        """..."""
        super(Configuration, self).__init__(
            module_name="FixMeToDo",
            models=(Fxtd,),
            analyses=("fxtd",),
            results_required=False,  # In this case,  Scans without data ARE valid!
        )

    def get_ingest_command(self, project_path: str, _) -> list[str]:
        """Return the command sent to subprocess to directly perform the scan operation."""
        return [
            "ruff",
            "check",
            "--exit-zero",
            "--output-format=json",
            project_path,
        ]

    def get_ingest_method(self, _) -> Callable:
        """Return the ingest method to parse and save the output."""
        py_ingest = import_module(f"mq.tools.{self.module_name}.ingest")  # eg. .../<module>/ingest.py
        return getattr(py_ingest, "ingest")
