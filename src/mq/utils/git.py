"""..."""

import logging
import subprocess
import tempfile
from argparse import Namespace
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator
from urllib.parse import urlparse

log = logging.getLogger(__name__)


def get_git_commit_hash() -> str:
    try:
        result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "unknown"  # Not in git repo or git not available


def checkout_commit(repo_path: Path, commit_hash: str) -> None:
    """Checkout a specific commit."""
    subprocess.run(["git", "checkout", "-f", commit_hash], cwd=repo_path, capture_output=True, check=True)


def git_commits(args: Namespace, revision_skip: int = 1) -> Iterator[tuple]:
    """Clone repo and analyze each revision."""
    args.git = args.git

    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / args.project
        log.debug(f"Repo path {repo_path}...")

        # Clone the repository
        log.debug(f"Cloning {args.git}...")
        subprocess.run(["git", "clone", args.git, str(repo_path)], check=True, capture_output=True)

        # Get all commits
        commits: list[str] = get_commit_hashes(repo_path)
        log.debug(f"Found {len(commits)} commits")

        # Process each commit
        for i, commit_info in enumerate_skip(commits, revision_skip):
            commit_hash, commit_date = commit_info
            log.debug(f"Processing commit {i + 1:02d}/{len(commits):d}: {commit_date} {commit_hash[:8]}")
            checkout_commit(repo_path, commit_hash)
            yield repo_path, commit_date, commit_hash


def get_commit_hashes(repo_path: Path) -> list[tuple[str, str]]:
    """Get all commit hashes in chronological order (oldest to newest)."""
    result = subprocess.run(
        ["git", "log", "--reverse", "--pretty=format:%H|%at"],  # Unix timestamp..
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=True,
    )
    commits = []
    for line in result.stdout.strip().split("\n"):
        hash_val, s_date = line.split("|")
        utc_date = datetime.fromtimestamp(int(s_date), tz=timezone.utc)
        commits.append((hash_val, utc_date))

    return commits


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


def enumerate_skip(items: list, skip: int) -> list[tuple[int, any]]:
    """Enumerate with skipping, but always include first and last items.

    Args:
        items: List to enumerate
        skip: Take every Nth item (skip=1 means all items, skip=2 means every other, etc.)

    Returns:
        List of tuples (index, item) where index maintains sequential numbering
    """
    n = len(items)

    if n == 0:
        return []

    if n == 1:
        return [(0, items[0])]

    # Track which indices we'll include
    indices = set()

    # Always include first
    indices.add(0)

    # Always include last
    indices.add(n - 1)

    # Add every skip-th item
    for i in range(0, n, skip):
        indices.add(i)

    # Build result in order
    result = []
    for i in sorted(indices):
        result.append((i, items[i]))

    return result
