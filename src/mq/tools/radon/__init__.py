"""Radon Module Configuration."""

from importlib import import_module
from typing import Callable

from mq.tools import AbstractModuleConfiguration
from mq.tools.radon.models import RadonCc, RadonHal, RadonMi, RadonRaw

TOOL: str = "radon"


class Configuration(AbstractModuleConfiguration):
    """Configure semantics associated with using the various Radon tools."""

    def __init__(self):
        """..."""
        super(Configuration, self).__init__(module="radon", analyses=("cc", "hal", "mi", "raw"))

    def get_models(self):
        """Return the models associated with the tool by analysis."""
        return dict(
            cc=RadonCc,
            hal=RadonHal,
            mi=RadonMi,
            raw=RadonRaw,
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
        py_parse = import_module(f"mq.tools.{self.module}.parse")  # eg. .../<module>/parse.py
        return getattr(py_parse, parse_method_name)  # eg. parse_json()
