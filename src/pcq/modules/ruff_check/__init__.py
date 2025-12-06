"""..."""

import json
import sys
from argman.argman import _ArgResult
from peewee import fn, SqliteDatabase
from rich import print
from rich.console import Console
from rich.table import Table

from pcq.models import Run
from pcq.modules.ruff_check.models import remove_common_prefixes, RuffCheck
from pcq.utilities.git import get_git_commit_hash


def ingest(args: _ArgResult, db: SqliteDatabase) -> None:
    gch = get_git_commit_hash()
    run = Run(git_commit_hash=gch, run_module="ruff_check")
    run.save()

    if not sys.stdin.isatty():
        # Pipeline mode - parse JSON from stdin
        data = json.loads(sys.stdin.read())
        ruff_checks = _parse_ruff_json(data)
        num = _save_results(run, ruff_checks)
        print(f"Ingested {num} results from ruff check.")
    else:
        print("We're not ready for this yet!")
        # Direct mode - run ruff ourselves
        # result = subprocess.run(["ruff", "check", "--output-format=json"] + user_args, capture_output=True)
        # data = json.loads(result.stdout)


def _parse_ruff_json(data: list) -> list[RuffCheck]:
    def _json_to_row(ruff_check_result: dict) -> RuffCheck:
        return RuffCheck(
            filename=ruff_check_result["filename"],
            line=ruff_check_result["location"]["row"],
            column=ruff_check_result["location"]["column"],
            message=ruff_check_result["message"],
            rule_code=ruff_check_result["code"],
        )

    return [_json_to_row(check) for check in data]


def _save_results(run: Run, rows: list[RuffCheck]) -> int:
    for row in rows:
        row.run_id = run.id
        row.save()
    return len(rows)


def report(args: _ArgResult, db: SqliteDatabase) -> None:
    run = Run.select().order_by(Run.timestamp.desc()).first()
    if not run:
        print("No runs yet.")
        return
    if args.report.verbosity == 0:
        count = RuffCheck.select().where(RuffCheck.run_id == run).count()
        print(f"{run.timestamp_local} : {count} ruff check issues encountered.")
    elif args.report.verbosity == 1:
        results = (
            RuffCheck.select(RuffCheck.rule_code, RuffCheck.message, fn.COUNT(RuffCheck.id).alias("count"))
            .where(RuffCheck.run_id == run)
            .group_by(RuffCheck.rule_code)
            .order_by(fn.COUNT(RuffCheck.id).desc())
        )
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Rule")
        table.add_column("Count", justify="center")
        table.add_column("Message")
        for result in results:
            table.add_row(result.rule_code, str(result.count), result.message)
        Console().print(table)

    elif args.report.verbosity == 2:
        print(f"{run.timestamp_local} : Following ruff checks encountered:")
        rows = RuffCheck.select().where(RuffCheck.run_id == run).order_by(RuffCheck.filename, RuffCheck.rule_code)
        foobar = 1
        rows = remove_common_prefixes(rows)
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Rule")
        table.add_column("File (line)")
        table.add_column("Message")
        for row in rows:
            table.add_row(row.rule_code, f"{row.filename} [{row.line}] ", row.message)
        Console().print(table)
