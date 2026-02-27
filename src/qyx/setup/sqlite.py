"""Setup our database and register both our base and all our tool models."""

import atexit
import logging
from argparse import Namespace
from pathlib import Path

from peewee import SqliteDatabase
from platformdirs import user_data_dir

from qyx.tools.base import Project, Request, Scan, State


def setup_sqlite(args: Namespace) -> None:
    """Setup our db store, setting the db connection into args for subsequent use."""
    if "tools" not in args:
        raise RuntimeError("Sorry, setup/tools.py must have already been run before we can setup the database!")

    db_path = Path(user_data_dir("qyx")) / "db.sqlite3"  # Normal path..
    db_path = getattr(args, "db_path", db_path)  # Override primarily used to override db path for testing!

    # Only create parent directory for file-based databases
    db_path_name: str = db_path
    if db_path != ":memory:" and not str(db_path).startswith("file:"):
        db_path_name = db_path.name
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    db_ = SqliteDatabase(db_path, pragmas={"autocommit": True, "check_same_thread": False, "foreign_keys": 1})

    # Now that we've created our connection, register to cleanly close it on exit.
    atexit.register(lambda: db_.close() if not db_.is_closed() else None)

    # Make sure our models have tables defined for 'em!
    models = [Project, Request, Scan, State]  # Base models first...
    for o_tool in args.tools.tools():  # Followed by tool-specific storage models
        for tool_peewee_classes in o_tool.models.values():
            for tool_peewee_class in tool_peewee_classes:
                models.append(tool_peewee_class)

    # CORE! Tie the models defined to our database instance
    for model_class in models:
        model_class._meta.database = db_
        model_class.create_table(safe=True)

    log = logging.getLogger(__name__)
    args._db = db_  # Set for subsequent use (very few places though)
    log.info(f"...connected to {db_path_name=} with {len(models)} models defined.")
