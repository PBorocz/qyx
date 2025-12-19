"""Ingest data obo running 'cloc' tool."""

import json
import subprocess
import sys
from argparse import Namespace
from pathlib import Path

from rich import print

from mq.modules.cloc import MODULE
from mq.modules.cloc.models import Cloc
from mq.modules.models import Project, Run
from mq.utils.git import get_git_commit_hash


def ingest(args: Namespace) -> None:
    gch = get_git_commit_hash()
    project = Project.get_or_insert(args.project)
    run = Run(project=project.id, module=MODULE, git_commit_hash=gch)
    run.save()

    if args.stdin:
        # Pipeline mode - parse JSON from stdin
        data = json.loads(sys.stdin.read())
    else:
        # Direct mode - run cloc ourselves
        result = subprocess.run(
            ["cloc", "--include-lang=Python", "--by-file", "--json", "--exclude-dir=.venv", args.project],
            capture_output=True,
        )
        data = json.loads(result.stdout)

    results = _parse_json(data)
    num = _save_results(run, results)
    print(f"[green]✓ Ingested [bold]{num}[/bold] results from {MODULE.upper()}[/green]")


def _parse_json(data: dict) -> list[Cloc]:
    def _json_to_row(fn_: str, cloc_result: dict) -> Cloc:
        fn_path = Path(fn_)
        assert fn_path.name
        return Cloc(
            dir=fn_path.parent,
            filename=fn_path.name,
            lines_blank=cloc_result["blank"],
            lines_code=cloc_result["code"],
            lines_comment=cloc_result["comment"],
        )

    return [_json_to_row(fn_, check) for fn_, check in data.items() if fn_ not in ("header", "SUM")]


def _save_results(run: Run, rows: list[Cloc]) -> int:
    for row in rows:
        row.run = run.id
        row.save()
    return len(rows)
