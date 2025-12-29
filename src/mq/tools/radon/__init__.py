"""Radon Module Configuration."""

from importlib import import_module
from typing import Callable

from mq.tools import AbstractModuleConfiguration
from mq.tools.radon.models import RadonCc, RadonHal, RadonHalFunction, RadonMi, RadonRaw

COLORS: dict = dict(positive="red", negative="green", neutral="white")


class Configuration(AbstractModuleConfiguration):
    """Configure semantics associated with using the various Radon tools."""

    def __init__(self):
        """..."""
        super(Configuration, self).__init__(
            module_name="radon",
            models=(RadonCc, RadonHal, RadonHalFunction, RadonMi, RadonRaw),
            analyses=("cc", "hal", "mi", "raw"),
        )

    def get_ingest_command(self, project_path: str, analysis: str) -> list[str]:
        """Return the command sent to subprocess to directly perform an ingest operation."""
        assert analysis, "Sorry, we need a sub_module here!"
        return [
            "uvx",
            "radon",
            analysis,
            "--json",
            project_path,
        ]

    def get_parse_method(self, analysis: str) -> Callable:
        """Return the parse method to parse this Radon analysis's JSON output."""
        parse_method_name = f"parse_json_{analysis.lower()}"
        py_parse = import_module(f"mq.tools.{self.module_name}.parse")  # eg. .../<module>/parse.py
        return getattr(py_parse, parse_method_name)  # eg. parse_json()
