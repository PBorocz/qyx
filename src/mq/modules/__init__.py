"""..."""

import importlib
import logging
import inspect
import sys
from pathlib import Path
from typing import Any

from peewee import Model

from mq.modules.base import Scan

log = logging.getLogger(__name__)


################################################################################################
def save_scan_results(scan: Scan, rows: list) -> int:
    for row in rows:
        row.scan = scan.id
        row.save()
    return len(rows)


################################################################################################
# "Setup" logic for dynamically identifying available modules and their respective db models.
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


# TODO: Refactor to reduce complexity..
def __get_modules_and_models() -> dict:  # noqa: C901
    """Introspect our modules directory to dynamically discover modules defined at run-time."""
    modules_dir = Path("src/mq/modules")
    module_information = {}

    # Iterate over /app/modules and get handles to each module
    for module_path in modules_dir.iterdir():
        log.debug(f"Evaluating {module_path=}...")
        if module_path.is_dir() and not module_path.name.startswith("_"):
            module_name = module_path.name
            log.debug(f"- {module_name=}...", file=sys.stderr)

            ################################################################################
            # Get a handle to the module itself.
            ################################################################################
            module = __get_module_from_path(module_name)

            ################################################################################
            # Import the models.py file from each module
            ################################################################################
            model_module = __get_model_from_module(module_name)
            log.debug(f"- {model_module=}...")

            ################################################################################
            # Find all classes that inherit from peewee.Model
            ################################################################################
            peewee_models = __get_peewee_models_from_models_module(model_module)
            log.debug(f"Found peewee models-> {peewee_models}")

            module_information[module_name] = {
                "module": module,  # eg. src/mq/modules/radon
                "models": peewee_models,  # eg. RadonCc, RadonHal, ...
                # "models_module": model_module,  # ie. src/mq/modules/<foo>/models.py
            }
    return module_information


MODULES_AND_MODELS = __get_modules_and_models()


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
