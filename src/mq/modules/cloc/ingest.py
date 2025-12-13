"""Ingest data obo running 'cloc' tool."""

import json
import sys
import subprocess
from pathlib import Path


from argparse import Namespace
from loguru import logger
from peewee import SqliteDatabase

from mq.modules.models import Project, Run
from mq.modules.cloc.models import Cloc
from mq.modules.cloc import MODULE
from mq.utilities.git import get_git_commit_hash


def ingest(args: Namespace) -> None:
    gch = get_git_commit_hash()
    project = Project.get_or_insert(args.project)
    run = Run(project_id=project.id, module=MODULE, git_commit_hash=gch)
    run.save()

    if not sys.stdin.isatty():
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
    logger.info(f"Ingested {num} results from {MODULE}.")


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
        row.run_id = run.id
        row.save()
    return len(rows)
