"""..."""

import json
import sys
from argman.argman import _ArgResult
from peewee import fn, SqliteDatabase
from rich import print
from rich.console import Console
from rich.table import Table

from pcq.models import Project, Run
from pcq.modules.ruff.models import remove_common_prefixes, Ruff
from pcq.utilities.git import get_git_commit_hash

MODULE = "ruff"


def ingest(args: _ArgResult, db: SqliteDatabase) -> None:
    gch = get_git_commit_hash()
    project = Project.get_or_insert(args.ingest.project)
    run = Run(project_id=project.id, module=MODULE, git_commit_hash=gch)
    run.save()

    if not sys.stdin.isatty():
        # Pipeline mode - parse JSON from stdin
        data = json.loads(sys.stdin.read())
        results = _parse_ruff_json(data)
        num = _save_results(run, results)
        print(f"Ingested {num} results from ruff check.")
    else:
        print("We're not ready for this yet!")
        # Direct mode - run ruff ourselves
        # result = subprocess.run(["ruff", "check", "--output-format=json"] + user_args, capture_output=True)
        # data = json.loads(result.stdout)


def _parse_ruff_json(data: list) -> list[Ruff]:
    def _json_to_row(ruff_result: dict) -> Ruff:
        return Ruff(
            filename=ruff_result["filename"],
            line=ruff_result["location"]["row"],
            column=ruff_result["location"]["column"],
            message=ruff_result["message"],
            rule_code=ruff_result["code"],
        )

    return [_json_to_row(check) for check in data]


def _save_results(run: Run, rows: list[Ruff]) -> int:
    for row in rows:
        row.run_id = run.id
        row.save()
    return len(rows)


def report(args: _ArgResult, db: SqliteDatabase) -> None:
    project = Project.get(source_dir=args.report.project)
    run = Run.select().order_by(Run.timestamp.desc()).where(Run.project_id == project.id, Run.module == MODULE).first()
    if not run:
        print("No runs yet.")
        return
    if args.report.verbosity == 0:
        results = (
            Ruff.select(Ruff.rule_code, Ruff.message, fn.COUNT(Ruff.id).alias("count"))
            .where(Ruff.run_id == run)
            .group_by(Ruff.rule_code)
            .order_by(fn.COUNT(Ruff.id).desc())
        )
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Rule")
        table.add_column("Count", justify="center")
        table.add_column("Message")
        for result in results:
            table.add_row(result.rule_code, str(result.count), result.message)
        Console().print(table)

    elif args.report.verbosity == 1:
        print(f"{run.timestamp_local} : Following ruff checks encountered:")
        rows = Ruff.select().where(Ruff.run_id == run).order_by(Ruff.filename, Ruff.rule_code)
        foobar = 1
        rows = remove_common_prefixes(rows)
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Rule")
        table.add_column("File (line)")
        table.add_column("Message")
        for row in rows:
            table.add_row(row.rule_code, f"{row.filename} [{row.line}] ", row.message)
        Console().print(table)
