"""..."""

from pathlib import Path
import json
import sys
import subprocess
from argman.argman import _ArgResult
from peewee import fn, SqliteDatabase
from rich import print
from rich.console import Console
from rich.table import Table

from pcq.models import Project, Run
from pcq.modules.radon.models import remove_common_prefixes, RadonRaw
from pcq.utilities.git import get_git_commit_hash

MODULE = "radon"


def ingest(args: _ArgResult, db: SqliteDatabase) -> None:
    gch = get_git_commit_hash()
    project = Project.get_or_insert(args.ingest.project)
    run = Run(project_id=project.id, module=MODULE, sub_module=args.ingest.submodule, git_commit_hash=gch)
    run.save()

    if not sys.stdin.isatty():
        # Pipeline mode - parse JSON from stdin
        data = json.loads(sys.stdin.read())
    else:
        # Direct mode - run radon ourselves
        sub_out = subprocess.run(["uvx", "radon", args.ingest.submodule, ".", "--json"], capture_output=True)
        data = json.loads(sub_out.stdout)

    if args.ingest.submodule == "raw":
        results = _parse_radon_raw_json(data)
    else:
        print(f"Sorry, we don't support submodule: {args.ingest.submodule} yet!")

    num = _save_results(run, results)
    print(f"Ingested {num} results from radon check.")


def _parse_radon_raw_json(data: dict[str, int]) -> list[RadonRaw]:
    def _json_to_row(fn_: str, radon_result: dict[str, int]) -> RadonRaw:
        fn_path = Path(fn_)
        return RadonRaw(
            dir=fn_path.parent,
            filename=fn_path.name,
            loc=radon_result["loc"],
            lloc=radon_result["lloc"],
            sloc=radon_result["sloc"],
            comments=radon_result["comments"],
            multi=radon_result["multi"],
            blank=radon_result["blank"],
            single_comments=radon_result["single_comments"],
        )

    return [_json_to_row(fn_, results) for fn_, results in data.items()]


def _save_results(run: Run, rows: list[RadonRaw]) -> int:
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
            Radon.select(Radon.rule_code, Radon.message, fn.COUNT(Radon.id).alias("count"))
            .where(Radon.run_id == run)
            .group_by(Radon.rule_code)
            .order_by(fn.COUNT(Radon.id).desc())
        )
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Rule")
        table.add_column("Count", justify="center")
        table.add_column("Message")
        for result in results:
            table.add_row(result.rule_code, str(result.count), result.message)
        Console().print(table)

    elif args.report.verbosity == 1:
        print(f"{run.timestamp_local} : Following radon checks encountered:")
        rows = Radon.select().where(Radon.run_id == run).order_by(Radon.filename, Radon.rule_code)
        foobar = 1
        rows = remove_common_prefixes(rows)
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Rule")
        table.add_column("File (line)")
        table.add_column("Message")
        for row in rows:
            table.add_row(row.rule_code, f"{row.filename} [{row.line}] ", row.message)
        Console().print(table)
