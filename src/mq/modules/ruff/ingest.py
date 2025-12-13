"""..."""

import json
import subprocess
import sys
from argparse import Namespace
from pathlib import Path

from loguru import logger
from peewee import SqliteDatabase

from mq.modules.models import Project, Run
from mq.modules.ruff import MODULE
from mq.modules.ruff.models import Ruff
from mq.utilities.git import get_git_commit_hash


def ingest(args: Namespace) -> None:
    gch = get_git_commit_hash()
    project = Project.get_or_insert(args.project)
    run = Run(project_id=project.id, module=MODULE, git_commit_hash=gch)
    run.save()

    if not sys.stdin.isatty():
        # Pipeline mode - parse JSON from stdin
        json_data = json.loads(sys.stdin.read())
    else:
        # Direct mode - run ruff ourselves
        result = subprocess.run(
            ["ruff", "check", "--output-format=json", args.project],
            capture_output=True,
        )
        json_data = json.loads(result.stdout)

    results = _parse_ruff_json(json_data)
    num = _save_results(run, results)
    logger.info(f"Ingested {num} results from ruff check.")


def _parse_ruff_json(data: list) -> list[Ruff]:
    def _json_to_row(ruff_result: dict) -> Ruff:
        fn_path = Path(ruff_result["filename"])
        return Ruff(
            dir=fn_path.parent,
            filename=fn_path.name,
            line=ruff_result["location"]["row"],
            column=ruff_result["location"]["column"],
            message=ruff_result["message"],
            rule_code=ruff_result["code"],
            url=ruff_result["url"],
        )

    return [_json_to_row(check) for check in data]


def _save_results(run: Run, rows: list[Ruff]) -> int:
    for row in rows:
        row.run_id = run.id
        row.save()
    return len(rows)
