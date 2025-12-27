"""..."""

import logging
import tempfile
import subprocess
from argparse import Namespace
from pathlib import Path
from typing import Iterator
from urllib.parse import urlparse

log = logging.getLogger(__name__)


def parse_git_standalone(args: Namespace) -> None:
    repo_url = "https://github.com/psf/requests.git"
    repo_url = args.git

    # Extract project name from URL
    project_name = extract_repo_name(repo_url)
    log.debug(f"Project name: {project_name}")

    for metrics in analyze_repository(project_name, repo_url):
        log.debug(f"Commit {metrics['commit_hash'][:8]}: {metrics['total_lines']} lines")
        # Here you would store metrics in your SQLite database


def run_metrics(repo_path: Path, commit_hash: str) -> dict:
    """Run your metrics tool on the current checkout."""
    # Example: count lines in Python files
    result = subprocess.run(
        "find . -name '*.py' -print0 | xargs -0 wc -l",
        cwd=repo_path,
        shell=True,
        capture_output=True,
        text=True,
    )

    # Parse the output - last line has total
    lines = result.stdout.strip().split("\n")
    total_lines = 0
    if lines and "total" in lines[-1]:
        total_lines = int(lines[-1].split()[0])

    return {"commit_hash": commit_hash, "total_lines": total_lines, "raw_output": result.stdout}


def analyze_repository(project_name: str, repo_url: str) -> Iterator[dict]:
    """Clone repo and analyze each revision.

    Args:
        project_name: Name of the project
        repo_url: GitHub repository URL

    Yields:
        Dictionary with metrics for each commit
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / project_name
        log.debug(f"Repo path {repo_path}...")

        # Clone the repository
        log.debug(f"Cloning {repo_url}...")
        subprocess.run(["git", "clone", repo_url, str(repo_path)], check=True, capture_output=True)

        # Get all commits
        commits: list[str] = get_commit_hashes(repo_path)
        log.debug(f"Found {len(commits)} commits")

        # Process each commit
        for i, commit_hash in enumerate_skip(commits, 10):
            log.debug(f"Processing commit {i + 1:02d}/{len(commits):d}: {commit_hash[:8]}")

            checkout_commit(repo_path, commit_hash)
            metrics = run_metrics(repo_path, commit_hash)
            yield metrics
