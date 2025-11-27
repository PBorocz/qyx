"""Primary driver script."""

import sys
from pathlib import Path

from argman import ArgMan
from argman.argman import _ArgResult
from peewee import SqliteDatabase

from pcq.models import Run, RuffCheck


def _setup_sqlite(args: _ArgResult) -> None:
    models = [Run, RuffCheck]
    db_path = Path("__data__/db.sqlite3")
    db = SqliteDatabase(db_path, pragmas={"autocommit": True, "check_same_thread": False})
    db.bind(models)
    db.connect()
    print(f"...connected to {db_path.name=} with {len(models)} models defined.")
    return db


def main():
    am = ArgMan()
    ingest_cmd = am.add_cmd("ingest")
    ingest_cmd.arg_str(long="source", default="ruff_check", desc="A description")
    args = am.parse()
    print(f"{type(args)=}")

    db = _setup_sqlite(args)

    if args.sub_cmd == "ingest":
        if args.ingest.source == "ruff_check":
            from pcq.modules import ruff_check

            ruff_check.ingest(args, db)
        else:
            print(f"Sorry, we don't know how to ingest from {args.ingest.source} yet!")

    elif args.sub_cmd == "report":
        print("Report...")
    else:
        print("Sorry, you must provide a base command to execute.")
        sys.exit(1)


if __name__ == "__main__":
    main()
