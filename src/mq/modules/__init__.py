"""..."""

import importlib
import logging
import inspect
import sys
from pathlib import Path

from peewee import Model

log = logging.getLogger(__name__)


# TODO: Refactor to reduce complexity..
def __get_modules_and_models(debug: bool = True) -> dict:  # noqa: C901
    modules_dir = Path("src/mq/modules")
    results = {}

    # Iterate over /app/modules and get handles to each module
    for module_path in modules_dir.iterdir():
        if debug:
            print(f"Evaluating {module_path=}...", file=sys.stderr, flush=True)
        if module_path.is_dir() and not module_path.name.startswith("_"):
            module_name = module_path.name
            try:
                if debug:
                    print(f"- {module_name=}...", file=sys.stderr, flush=True)

                # Import the models.py file from each module
                models_module = importlib.import_module(f"mq.modules.{module_name}.models")
                if debug:
                    print(f"- {models_module=}...", file=sys.stderr, flush=True)

                # Find all classes that inherit from peewee.Model
                peewee_models = []
                for name, obj in inspect.getmembers(models_module, inspect.isclass):
                    if debug:
                        print(f"-- {name=}...", file=sys.stderr, flush=True)
                    # Check if the class is defined in this module (not imported)
                    if obj.__module__ == models_module.__name__:
                        # Check if it inherits from peewee.Model
                        if issubclass(obj, Model) and obj is not Model:
                            peewee_models.append(obj)
                            if debug:
                                print(f"-- {obj.__name__=} is a peewee model!", file=sys.stderr, flush=True)

                results[module_name] = {"module": models_module, "models": peewee_models}

            except ImportError as e:
                log.error(f"Could not import models from {module_name}: {e}")
                results[module_name] = {"module": None, "models": []}
    return results


__MODULES_AND_MODELS = __get_modules_and_models(debug=False)

# Also create "flattened" versions for various uses (one of strings and the other of peewee models)
MODULES: list[str] = sorted([module_name for module_name in __MODULES_AND_MODELS.keys()])

MODULE_MODELS: list[list] = []
for data in __MODULES_AND_MODELS.values():
    MODULE_MODELS.extend(data["models"])


def models_for_module(module: str) -> list[Model]:
    return __MODULES_AND_MODELS[module]["models"]
