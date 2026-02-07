"""Setup our database and register both our base and all our tool models."""

import logging
from argparse import Namespace
from pathlib import Path

from peewee import SqliteDatabase
from platformdirs import user_data_dir

from mq.tools.base import Project, Request, Scan


def setup_sqlite(args: Namespace) -> None:
    """Setup our db store, setting the db connection into args for subsequent use."""
    if "tools" not in args:
        raise RuntimeError("Sorry, setup/tools.py must have already been run before we can setup the database!")

    db_path = Path(user_data_dir("mq")) / "mq.sqlite3"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_ = SqliteDatabase(db_path, pragmas={"autocommit": True, "check_same_thread": False, "foreign_keys": 1})

    # Make sure our models have tables defined for 'em!
    models = [Project, Request, Scan]
    for o_tool in args.tools.values():
        for tool_peewee_classes in o_tool.models.values():
            for tool_peewee_class in tool_peewee_classes:
                models.append(tool_peewee_class)

    for model_class in models:
        model_class._meta.database = db_
        model_class.create_table(safe=True)

    log = logging.getLogger(__name__)
    args._db = db_  # Set for subsequent use (very few places though)
    log.debug(f"...connected to {db_path.name=} with {len(models)} models defined.")
