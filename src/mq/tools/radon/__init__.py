"""Radon Module Configuration."""

from importlib import import_module
from typing import Callable

from mq.tools.base import AbstractModuleConfiguration
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

    def get_ingest_command(self, relative: str = None, absolute: str = None, analysis: str = None) -> list[str]:
        """Return the command sent to subprocess to directly perform an ingest operation."""
        assert analysis, "Sorry, we need a sub_module here!"
        return [
            "uvx",
            "radon",
            analysis,
            "--json",
            absolute,
        ]

    def get_ingest_method(self, analysis: str) -> Callable:
        """Return the ingest method to parse & save this Radon analysis's JSON output."""
        py_ingest = import_module(f"mq.tools.{self.module_name}.ingest")  # eg. .../<module>/ingest.py
        ingest_method_name = f"ingest_{analysis.lower()}"
        return getattr(py_ingest, ingest_method_name)  # eg. ingest_cc()
