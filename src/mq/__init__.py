"""."""

import argparse
import logging
import tomllib
from argparse import Namespace
from pathlib import Path
from platformdirs import user_config_dir

from peewee import SqliteDatabase
from platformdirs import user_data_dir
from rich.console import Console
from rich.logging import RichHandler

from mq.tools.base import Project, Request, Scan


################################################################################################
def setup_configuration(app_name: str = "mq") -> tuple[argparse.ArgumentParser, list[str], dict]:
    configuration_parser = argparse.ArgumentParser(add_help=False)
    configuration_parser.add_argument("-c", "--config", type=Path)
    config_args, remaining_args = configuration_parser.parse_known_args()  # Note method used here!

    if config_args.config:
        configuration = _load_config(config_args.config)
    else:
        configuration = _find_and_load_config(app_name)

    # Irrespective of which source, return the parser and configuration settings (if any!)
    return configuration_parser, remaining_args, configuration


def _load_config(config_path: Path | None) -> dict:
    """Load user's configuration from the specified path."""
    if not config_path:
        return {}

    if not config_path.exists():
        raise FileNotFoundError(f"Sorry, we couldn't find a configuration file at: {config_path}")

    with open(config_path, "rb") as fh_:
        return tomllib.load(fh_)


def _find_and_load_config(app_name: str, filename: str = "config.toml") -> dict:
    """Find and load config from either of two possible locations: `cwd` and user config dir."""
    # Current directory?
    current = Path.cwd() / filename
    if current.exists():
        return _load_config(current)

    # User config directory for our app?
    config_path = Path(user_config_dir(app_name)) / filename
    if config_path.exists():
        return _load_config(config_path)

    return {}


################################################################################################
def setup_logging(arg_log_level: str, arg_peewee_debug: bool = False) -> logging.Logger:
    level = getattr(logging, arg_log_level.upper())
    peewee_level = "DEBUG" if arg_peewee_debug else "INFO"

    # Setup Rich handler
    console = Console()
    rich_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=True,
        rich_tracebacks=True,
        tracebacks_show_locals=False,
    )
    rich_handler.setFormatter(logging.Formatter(fmt="%(message)s", datefmt="[%X]"))

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()  # Remove any existing handlers
    root_logger.setLevel(level)
    root_logger.addHandler(rich_handler)

    # Configure uvicorn logger specifically
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.handlers.clear()  # Remove uvicorn's default handlers
    uvicorn_logger.addHandler(rich_handler)
    uvicorn_logger.setLevel(level)
    uvicorn_logger.propagate = False  # Don't propagate to root to avoid duplicates

    # Also configure uvicorn.access if you want access logs formatted too
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.handlers.clear()
    access_logger.addHandler(rich_handler)
    access_logger.propagate = False

    # Configure Peewee logger explicitly
    peewee_logger = logging.getLogger("peewee")
    peewee_logger.handlers.clear()
    peewee_logger.addHandler(rich_handler)
    peewee_logger.setLevel(peewee_level)
    peewee_logger.propagate = False


################################################################################################
def setup_sqlite(args: Namespace) -> None:
    db_path = Path(user_data_dir("mq")) / "mq.sqlite3"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = SqliteDatabase(db_path, pragmas={"autocommit": True, "check_same_thread": False, "foreign_keys": 1})

    # Make sure our models have tables defined for 'em!
    models = [Project, Request, Scan]
    for configuration in args.tools.values():
        for tool_peewee_class in configuration.models.values():
            models.append(tool_peewee_class)

    for model_class in models:
        model_class._meta.database = db
        model_class.create_table(safe=True)

    log = logging.getLogger(__name__)
    log.debug(f"...connected to {db_path.name=} with {len(models)} models defined.")
