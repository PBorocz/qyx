"""..."""

import logging
from abc import ABC, abstractmethod
from importlib import import_module
from argparse import Namespace
from pathlib import Path

from mq.modules.base import Scan

log = logging.getLogger(__name__)


################################################################################################
class AbstractModuleConfiguration(ABC):
    """Defines all the semantics of a code quality tool (aka Module) supported by this package."""

    def __init__(
        self,
        module_name: str,
        sub_modules: tuple[str],
        **kwargs,
    ) -> "AbstractModuleConfiguration":
        """..."""
        self.module_name = module_name
        self.sub_modules: tuple[str] = sub_modules  # List of sub_modules (even if just 1 for stuff like cloc and ruff)
        self.results_required = True  # Are Results "required" for a Scan to be valid? (usually yes)

        for attr, value in kwargs.items():
            setattr(self, attr, value)

    def get_ingest_command(self, *args, **kwargs):
        """..."""
        raise NotImplementedError("Sorry, this method needs to be implemented by an inherited class!")

    def get_parse_methods(self, *args, **kwargs):
        """..."""
        raise NotImplementedError("Sorry, this method needs to be implemented by an inherited class!")


################################################################################################
def save_scan_results(scan: Scan, rows: list) -> int:
    for row in rows:
        row.scan = scan.id
        row.save()
    return len(rows)


################################################################################################
# "Setup" logic for dynamically identifying available modules and their respective configurations
################################################################################################
def setup_modules(args: Namespace) -> dict:
    """Introspect our modules directory to dynamically discover modules defined at run-time."""
    modules = {}

    # Iterate over /app/modules and get handles to each module
    modules_dir = Path("src/mq/modules")
    for module_path in modules_dir.iterdir():
        if module_path.is_dir() and not module_path.name.startswith("_"):
            module_name = module_path.name
            log.debug(f"Setting up module: '{module_name}'...")

            ################################################################################
            # Get a handle to the module itself.
            ################################################################################
            try:
                s_import_path = f"mq.modules.{module_name}"
                module = import_module(s_import_path)
            except ImportError as exc:
                raise RuntimeError(f"Sorry, can't import: '{s_import_path}': {exc}!")

            ################################################################################
            # Now, find the configuration Class
            ################################################################################
            try:
                module_class = getattr(module, "Configuration")
                log.debug(f"{module_class=}")
            except AttributeError as exc:
                raise RuntimeError(f"Sorry, can't instantiate {module_name}'s configuration class?: {exc}!")

            ################################################################################
            # ...instantiate it and store it!
            ################################################################################
            modules[module_name] = module_class()

    log.debug(f"Modules available: {', '.join(modules.keys())}")
    return modules


################################################################################################
# Misc. utilities functions
################################################################################################
def format_int_or_percentage(value, as_percentage):
    return f"{value:.0f}%" if as_percentage else f"{value:,}"
