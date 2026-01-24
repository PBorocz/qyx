"""Radon Module Configuration."""

import types
from typing import Callable

from mq.tools.base import AbstractToolConfiguration
from mq.tools.radon.models import RadonCc, RadonHal, RadonHalFunction, RadonMi, RadonRaw

COLORS: dict = dict(positive="red", negative="green", neutral="white")


class Configuration(AbstractToolConfiguration):
    """Configure semantics associated with using the various Radon tools."""

    def __init__(self):
        """..."""
        super(Configuration, self).__init__(
            module_name="radon",
            models=dict(
                cc=RadonCc,
                hal=RadonHal,
                _hal=RadonHalFunction,
                mi=RadonMi,
                raw=RadonRaw,
            ),
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
        py_ingest: types.ModuleType = self.import_component("ingest")  # eg. .../<module>/ingest.py
        return getattr(py_ingest, f"ingest_{analysis.lower()}")  # eg. ingest_cc()
