"""..."""

import json
import sys
import subprocess
from collections import defaultdict
from pathlib import Path


from argman.argman import _ArgResult
from peewee import fn, SqliteDatabase
from rich import print
from rich.console import Console
from rich.table import Table

from pcq.models import Project, Run
from pcq.modules.cloc.models import Cloc
from pcq.utilities.git import get_git_commit_hash

MODULE = "cloc"


def ingest(args: _ArgResult, db: SqliteDatabase) -> None:
    gch = get_git_commit_hash()
    project = Project.get_or_insert(args.ingest.project)
    run = Run(project_id=project.id, module=MODULE, git_commit_hash=gch)
    run.save()

    if not sys.stdin.isatty():
        # Pipeline mode - parse JSON from stdin
        data = json.loads(sys.stdin.read())
    else:
        # Direct mode - run cloc ourselves
        result = subprocess.run(["cloc", "--include-lang=Python", "--by-file", "--json", "src/"], capture_output=True)
        data = json.loads(result.stdout)

    results = _parse_json(data)
    num = _save_results(run, results)
    print(f"Ingested {num} results from {MODULE}.")


def _parse_json(data: dict) -> list[Cloc]:
    def _json_to_row(fn_: str, cloc_result: dict) -> Cloc:
        fn_path = Path(fn_)
        return Cloc(
            dir=fn_path.parent,
            file_name=fn_path.name,
            lines_blank=cloc_result["blank"],
            lines_code=cloc_result["code"],
            lines_comment=cloc_result["comment"],
        )

    return [_json_to_row(fn_, check) for fn_, check in data.items() if fn_ not in ("header", "SUM")]


def _save_results(run: Run, rows: list[Cloc]) -> int:
    for row in rows:
        row.run_id = run.id
        row.save()
    return len(rows)


def report(args: _ArgResult, db: SqliteDatabase) -> None:
    project = Project.get(source_dir=args.report.project)
    run = Run.select().order_by(Run.timestamp.desc()).where(Run.project_id == project.id, Run.module == MODULE).first()
    # run = Run.select().order_by(Run.timestamp.desc()).where(Run.module == MODULE).first()
    if not run:
        print("No runs yet.")
        return

    if args.report.verbosity == 0:
        results = Cloc.select(
            fn.SUM(Cloc.lines_blank).alias("lines_blank"),
            fn.SUM(Cloc.lines_code).alias("lines_code"),
            fn.SUM(Cloc.lines_comment).alias("lines_comment"),
        ).get()
        table = Table(
            title=f"cloc: {run.timestamp_local}",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Code", justify="right")
        table.add_column("Comment", justify="right")
        table.add_column("Blank", justify="right")
        table.add_row(
            f"{results.lines_code}",
            f"{results.lines_comment}",
            f"{results.lines_blank}",
        )
        Console().print(table)

    elif args.report.verbosity == 1:
        rows = Cloc.select().where(Cloc.run_id == run).order_by(Cloc.dir, Cloc.file_name)
        sums = defaultdict(int)
        for row in rows:
            sums["blank"] += row.lines_blank
            sums["comment"] += row.lines_comment
            sums["code"] += row.lines_code

        table = Table(
            title=f"cloc: {run.timestamp_local}",
            show_header=True,
            show_footer=True,
            header_style="bold magenta",
        )
        table.add_column("File", footer="Total")
        table.add_column("Code", justify="right", footer=str(sums["code"]))
        table.add_column("Comment", justify="right", footer=str(sums["comment"]))
        table.add_column("Blank", justify="right", footer=str(sums["blank"]))
        for row in rows:
            table.add_row(
                f"{row.dir}/{row.file_name}",
                str(row.lines_code),
                str(row.lines_comment),
                str(row.lines_blank),
            )
        Console().print(table)
