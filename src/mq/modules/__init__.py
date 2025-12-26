"""..."""

import importlib
import logging
import inspect
import sys
from argparse import Namespace
from pathlib import Path
from typing import Any

from peewee import Model

from mq.modules.base import Scan

log = logging.getLogger(__name__)


################################################################################################
class AbstractModuleConfiguration:
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
        raise RuntimeError("Sorry, this method needs to be implemented by an inherited class!")

    def get_parse_methods(self, *args, **kwargs):
        """..."""
        raise RuntimeError("Sorry, this method needs to be implemented by an inherited class!")


################################################################################################
def save_scan_results(scan: Scan, rows: list) -> int:
    for row in rows:
        row.scan = scan.id
        row.save()
    return len(rows)


################################################################################################
# "Setup" logic for dynamically identifying available modules and their respective configurations
################################################################################################
def __get_module_from_path(module_name: str) -> Any:
    try:
        return importlib.import_module(f"mq.modules.{module_name}")
    except ImportError as e:
        raise RuntimeError(f"Could not import {module_name=}: {e}!")


def __get_model_from_module(module_name: str) -> []:
    try:
        return importlib.import_module(f"mq.modules.{module_name}.models")
    except ImportError as e:
        raise RuntimeError(f"Could not import models.py {module_name=}: {e}")


def __get_peewee_models_from_models_module(model_module) -> []:
    peewee_models = []
    for name, obj in inspect.getmembers(model_module, inspect.isclass):
        # Check if the class is defined in this module (not imported)
        if obj.__module__ == model_module.__name__:
            # Check if it inherits from peewee.Model
            if issubclass(obj, Model) and obj is not Model:
                peewee_models.append(obj)
    return peewee_models


MODULES = None


# TODO: Refactor to reduce complexity..
def setup_modules(args: Namespace) -> dict:  # noqa: C901
    """Introspect our modules directory to dynamically discover modules defined at run-time."""
    global MODULES
    MODULES = {}

    # Iterate over /app/modules and get handles to each module
    modules_dir = Path("src/mq/modules")
    for module_path in modules_dir.iterdir():
        log.debug(f"Evaluating {module_path=}...")
        if module_path.is_dir() and not module_path.name.startswith("_"):
            module_name = module_path.name
            log.debug(f"- {module_name=}...")

            ################################################################################
            # Get a handle to the module itself.
            ################################################################################
            module = __get_module_from_path(module_name)

            try:
                module_class = getattr(module, "Configuration")
                log.debug(f"{module_class=}")
            except AttributeError:
                log.debug(f"{module=} NOT CONFIGURED YET, Skipping...")
                continue

            MODULES[module_name] = module_class()

            ################################################################################
            # Import the models.py file from each module
            ################################################################################
            # model_module = __get_model_from_module(module_name)
            # log.debug(f"- {model_module=}...")

            ################################################################################
            # Find all classes that inherit from peewee.Model
            ################################################################################
            # peewee_models = __get_peewee_models_from_models_module(model_module)
            # log.debug(f"Found peewee models-> {peewee_models}")

            # module_information[module_name] = {
            #     "module": module,  # eg. src/mq/modules/radon
            #     "models": peewee_models,  # eg. RadonCc, RadonHal, ...
            #     # "models_module": model_module,  # ie. src/mq/modules/<foo>/models.py
            # }

    log.info(f"Modules available: {', '.join(MODULES.keys())}")
    return MODULES


# MODULES_AND_MODELS = __get_modules_and_models()
MODULES_AND_MODELS = {}


def models_for_module(module: str) -> list[Model]:
    """Return peewee data model classes associated with the specified module name."""
    return MODULES_AND_MODELS[module]["models"]


################################################################################################
# Create "flattened" versions for various uses (one of strings and the other of peewee models)
################################################################################################
MODULE_NAMES: list[str] = sorted([module_name for module_name in MODULES_AND_MODELS.keys()])
log.debug(f"Introspected the following modules {','.join(MODULE_NAMES)}")

################################################################################################
# Make available the list of peewee model class definitions across all available modules.
################################################################################################
MODULE_MODELS: list[list] = list()
for data in MODULES_AND_MODELS.values():
    MODULE_MODELS.extend(data["models"])


################################################################################################
# Misc. utilities functions
################################################################################################
def format_int_or_percentage(value, as_percentage):
    return f"{value:.0f}%" if as_percentage else f"{value:,}"
