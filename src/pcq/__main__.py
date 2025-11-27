"""Primary driver script."""

import logging
import sys
from pathlib import Path

from argman import ArgMan
from argman.argman import _ArgResult
from peewee import SqliteDatabase

from pcq.models import Run, RuffCheck
from pcq.modules import db as db_module


def _setup_sqlite(args: _ArgResult) -> None:
    models = [Run, RuffCheck]
    db_path = Path("__data__/db.sqlite3")
    db = SqliteDatabase(db_path, pragmas={"autocommit": True, "check_same_thread": False})
    db.bind(models)
    db.connect()
    logging.debug(f"...connected to {db_path.name=} with {len(models)} models defined.")
    return db


def main():
    am = ArgMan()
    ingest_cmd = am.add_cmd("ingest")
    ingest_cmd.arg_str(long="module", default="ruff_check", desc="Module to execute, e.g. ruff-check, source-lines etc")

    report_cmd = am.add_cmd("report")
    report_cmd.arg_str(long="module", default="ruff_check", desc="Module to report on.")
    report_cmd.arg_int(long="verbosity", default=0, desc="Verbosity/depth to report on (starting from 0 for top-level)")

    flush_cmd = am.add_cmd("flush")
    flush_cmd.arg_str(long="module", desc="Optional module to flush data for, e.g. ruff-check, source-lines etc")

    args = am.parse()

    db = _setup_sqlite(args)

    if args.sub_cmd == "ingest":
        if args.ingest.module == "ruff_check":
            from pcq.modules import ruff_check

            ruff_check.ingest(args, db)
        else:
            print(f"Sorry, we don't know how to ingest from {args.ingest.module} yet!")

    elif args.sub_cmd == "report":
        if args.report.module == "ruff_check":
            from pcq.modules import ruff_check

            ruff_check.report(args, db)
        else:
            print(f"Sorry, we don't know how to report on data from {args.report.module} yet!")

    elif args.sub_cmd == "flush":
        db_module.flush(args, db)

    else:
        print("Sorry, you must provide a base command to execute.")
        sys.exit(1)


if __name__ == "__main__":
    main()
