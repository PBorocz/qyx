"""."""

import sys
from argparse import Namespace
from pathlib import Path

from peewee import SqliteDatabase
from platformdirs import user_data_dir

from mq.modules import MODULE_MODELS
from mq.modules.models import Project, Run


def setup_sqlite(args: Namespace, logger) -> None:
    db_path = Path(user_data_dir("mq")) / "mq.sqlite3"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = SqliteDatabase(db_path, pragmas={"autocommit": True, "check_same_thread": False, "foreign_keys": 1})

    # Make sure our models have tables defined for 'em!
    for ith, model_class in enumerate([Project, Run] + MODULE_MODELS):
        model_class._meta.database = db
        model_class.create_table(safe=True)
    logger.debug(f"...connected to {db_path.name=} with {ith + 1} models defined.")


def setup_logging(args: Namespace, logger) -> None:
    logger.remove()
    log_level = "DEBUG" if args.debug else "INFO"
    # TODO: For production/packaging deploy: change diagnose to False
    logger.add(sys.stderr, level=log_level, backtrace=True, diagnose=True)
