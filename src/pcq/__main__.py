"""Primary driver script."""

import logging
import sys
from pathlib import Path

from argman import ArgMan
from argman.argman import _ArgResult
from peewee import SqliteDatabase
from rich import print

from pcq.models import Run
from pcq.modules import db as db_module
from pcq.modules.cloc.models import Cloc
from pcq.modules.radon.models import RadonRaw  # RadonCC, RadonMI, RadonHAL
from pcq.modules.ruff.models import Ruff


def _setup_sqlite(args: _ArgResult) -> None:
    models = [Run, Cloc, Ruff, RadonRaw]  # RadonCC, RadonMI, RadonHAL, RadonRAW
    db_path = Path("__data__/db.sqlite3")
    db = SqliteDatabase(db_path, pragmas={"autocommit": True, "check_same_thread": False, "foreign_keys": 1})
    db.bind(models)
    db.connect()
    logging.debug(f"...connected to {db_path.name=} with {len(models)} models defined.")
    return db


def main():
    am = ArgMan()
    cmd_i = am.add_cmd("ingest")
    cmd_i.arg_str(short="p", long="project", desc='Base path to project to ingest from, defaults to "."', default=".")
    cmd_i.arg_str(short="m", long="module", desc="Module to execute, e.g. radon, ruff, cloc etc")
    cmd_i.arg_str(short="s", long="submodule", desc="Optional sub-module, e.g. cc for Radon.")
    cmd_i.arg_int(short="v", long="verbosity", default=0, desc="Logging verbosity")

    cmd_r = am.add_cmd("report")
    cmd_r.arg_str(short="p", long="project", desc='Base path to project to report for, defaults to "."', default=".")
    cmd_r.arg_str(short="m", long="module", desc="Module to report on.")
    cmd_r.arg_str(short="s", long="submodule", desc="Optional sub-module, e.g. cc for Radon.")
    cmd_r.arg_int(
        short="v", long="verbosity", default=0, desc="Verbosity/depth to report (starting from 0 for top-level)"
    )

    flush_cmd = am.add_cmd("flush")
    flush_cmd.arg_str(long="module", desc="Optional module to flush data for, e.g. ruff, source-lines etc")

    args = am.parse()

    db = _setup_sqlite(args)

    if args.sub_cmd == "ingest":
        if args.ingest.module == "cloc":
            from pcq.modules import cloc

            cloc.ingest(args, db)
        elif args.ingest.module == "radon":
            from pcq.modules import radon

            radon.ingest(args, db)
        elif args.ingest.module == "ruff":
            from pcq.modules import ruff

            ruff.ingest(args, db)
        else:
            print(f"Sorry, we don't know how to ingest from {args.ingest.module} yet!")

    elif args.sub_cmd == "report":
        if args.report.module == "cloc":
            from pcq.modules import cloc

            cloc.report(args, db)
        elif args.report.module == "radon":
            from pcq.modules import radon

            radon.report(args, db)
        elif args.report.module == "ruff":
            from pcq.modules import ruff

            ruff.report(args, db)
        else:
            print(f"Sorry, we don't know how to report on data from {args.report.module} yet!")

    elif args.sub_cmd == "flush":
        db_module.flush(args, db)

    else:
        print("Sorry, you must provide a base command to execute.")
        sys.exit(1)


if __name__ == "__main__":
    main()
