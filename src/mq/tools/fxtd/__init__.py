"""FixMe ToDo Module Configuration."""

import logging
from pathlib import Path

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
            module_name="fxtd",
            models=(Fxtd,),
            analyses=("fxtd",),
            results_required=False,  # In this case,  Scans without data ARE valid!
        )

    def get_ingest_command(self, relative: str = None, absolute: str = None, analysis: str = None) -> list[str]:
        """Return the command sent to subprocess to directly perform the scan operation."""
        script_dir = Path(__file__).parent
        fxtd_script = script_dir / "fxtd.sh"
        assert fxtd_script.exists(), f"Sorry, we expected to find 'fxtd.sh' at {script_dir}!"
        return [str(fxtd_script), str(absolute)]

    def get_ingest_method(self, _) -> Callable:
        """Return the ingest method to parse and save the output."""
        py_ingest = import_module(f"mq.tools.{self.module_name}.ingest")  # eg. .../<module>/ingest.py
        return getattr(py_ingest, "ingest")
