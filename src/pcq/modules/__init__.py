"""..."""

import importlib
import inspect
from pathlib import Path

from loguru import logger
from peewee import Model


def __get_modules_and_models():
    modules_dir = Path("src/pcq/modules")
    results = {}

    # Iterate over /app/modules and get handles to each module
    for module_path in modules_dir.iterdir():
        if module_path.is_dir() and not module_path.name.startswith("_"):
            module_name = module_path.name

            try:
                # Import the models.py file from each module
                models_module = importlib.import_module(f"pcq.modules.{module_name}.models")

                # Find all classes that inherit from peewee.Model
                peewee_models = []
                for name, obj in inspect.getmembers(models_module, inspect.isclass):
                    # Check if the class is defined in this module (not imported)
                    if obj.__module__ == models_module.__name__:
                        # Check if it inherits from peewee.Model
                        if issubclass(obj, Model) and obj is not Model:
                            peewee_models.append(obj)

                results[module_name] = {"module": models_module, "models": peewee_models}

            except ImportError as e:
                logger.error(f"Could not import models from {module_name}: {e}")
                results[module_name] = {"module": None, "models": []}

    return results


__MODULES_AND_MODELS = __get_modules_and_models()

# Also create "flattened" versions for various uses (one of strings and the other of peewee models)
MODULES = [datum["module"].__name__ for datum in __MODULES_AND_MODELS.values()]
MODELS = []
for data in __MODULES_AND_MODELS.values():
    MODELS.extend(data["models"])


def models_for_module(module: str) -> list[Model]:
    return __MODULES_AND_MODELS[module]["models"]
