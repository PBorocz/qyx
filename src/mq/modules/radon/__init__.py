"""Radon Module Configuration."""

from importlib import import_module
from typing import Callable

from mq.modules import AbstractModuleConfiguration
from mq.modules.radon.models import RadonCc, RadonHal, RadonMi, RadonRaw

MODULE = "radon"


class Configuration(AbstractModuleConfiguration):
    """Configure semantics associated with using the various Radon tools."""

    def __init__(self):
        """..."""
        super(Configuration, self).__init__(module_name=MODULE, sub_modules=("cc", "hal", "mi", "raw"))

    def get_models(self):
        """Return the models associated with the module by sub_module."""
        return dict(
            cc=RadonCc,
            hal=RadonHal,
            mi=RadonMi,
            raw=RadonRaw,
        )

    def get_ingest_command(self, project_path: str, sub_module: str) -> list[str]:
        """Return the command sent to subprocess to directly perform an ingest operation."""
        assert sub_module, "Sorry, we need a sub_module here!"
        return [
            "uvx",
            "radon",
            sub_module,
            "--json",
            project_path,
        ]

    def get_parse_method(self, sub_module: str) -> Callable:
        """Return the parse method to parse this Radon sub_module's JSON output."""
        parse_method_name = f"parse_json_{sub_module.lower()}"
        py_parse = import_module(f"mq.modules.{self.module_name}.parse")  # eg. .../<module>/parse.py
        return getattr(py_parse, parse_method_name)  # eg. parse_json()
