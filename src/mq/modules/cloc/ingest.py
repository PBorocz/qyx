"""Ingest data obo running 'cloc' tool."""

import logging
import json
import subprocess
import sys
from argparse import Namespace
from pathlib import Path
from urllib.parse import urlparse

from rich import print

from mq.modules.cloc import MODULE
from mq.modules.cloc.git import git_commits
from mq.modules.cloc.models import Cloc
from mq.modules.base import Project, Run
from mq.utils.git import get_git_commit_hash


log = logging.getLogger(__name__)


def ingest(args: Namespace) -> None:
    if args.git:
        parse_git(args)
    else:
        parse_single(args)


def parse_git(args: Namespace) -> None:
    args.project = extract_repo_name(args.git)  # Note: we disregard any command-line project name provided!
    log.debug(f"Project name: {args.project}")

    project = Project.get_or_insert_raw(args.git, args.git, args.project)
    log.debug(f"Project: {project=}")

    for repo_path, commit_hash in git_commits(args):
        # Create the associated Run instance for this project
        run = Run.create(project=project.id, module=MODULE, git_commit_hash=commit_hash)
        log.debug(f"Run: {run=}")

        # Run cloc against our temporary repo checked out to the specified commit_hash
        result = subprocess.run(
            ["cloc", "--include-lang=Python", "--by-file", "--json", "--exclude-dir=.venv", "."],
            cwd=repo_path,
            capture_output=True,
            check=True,
        )
        data = json.loads(result.stdout)
        results = _parse_json(data)
        log.debug(f"{len(results)}")

        num = _save_results(run, results)
        print(f"[green]✓ Ingested [bold]{num}[/bold] results from {MODULE.upper()}[/green] ({commit_hash})")


def parse_single(args: Namespace) -> None:
    gch = get_git_commit_hash()
    project = Project.get_or_insert_relative(args.project)
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


def extract_repo_name(repo_url: str) -> str:
    """Extract repository name from GitHub URL."""
    # Handle both HTTPS and SSH URLs
    # https://github.com/user/repo.git -> repo
    # git@github.com:user/repo.git -> repo

    if repo_url.startswith("git@"):
        # SSH format: git@github.com:user/repo.git
        path = repo_url.split(":")[-1]
    else:
        # HTTPS format: https://github.com/user/repo.git
        parsed = urlparse(repo_url)
        path = parsed.path

    # Remove leading slash and .git suffix
    repo_name = path.strip("/").rstrip(".git")

    # Get just the repo name (last part after /)
    return repo_name.split("/")[-1]
