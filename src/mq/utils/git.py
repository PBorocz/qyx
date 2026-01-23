"""..."""

import logging
import subprocess
from argparse import Namespace
from datetime import datetime, timezone
from pathlib import Path
from platformdirs import user_cache_dir
from urllib.parse import urlparse

log = logging.getLogger(__name__)


def get_git_commit_hash() -> str:
    try:
        result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "unknown"  # Not in git repo or git not available


def get_git_commits(git_repo: str) -> tuple[Path, list[str]]:
    """Setup the git repository (cloning if necessary) and get the list of commit revisions."""
    repo_path = _get_repo_cache_dir(git_repo)

    # Do we need to clone "anew" or can we use an refresh to an existing cached repository?
    if repo_path.exists() and (repo_path / ".git").exists():
        # Yep, we still have it, refresh it!
        log.info(f"Updating existing repo at {repo_path}")
        subprocess.run(["git", "fetch", "origin"], cwd=repo_path, check=True)
    else:
        # Don't have it yet locally, clone it!
        log.info(f"Cloning '{git_repo}' into {repo_path}...")
        subprocess.run(["git", "clone", git_repo, str(repo_path)], check=True, capture_output=True)

    # Given the repo, find all commit hashes associated all revisions:
    commits: list[str] = _get_commit_hashes(repo_path)
    log.debug(f"{repo_path} has {len(commits)} commits")
    return repo_path, commits


def git_checkout(scan_request: Namespace) -> bool:
    """Perform a git checkout for the specified request (which has path and commit hash)."""
    log.debug(f"git checkout: {scan_request.as_of} {scan_request.hash[:8]}")
    try:
        subprocess.run(
            ["git", "checkout", "-f", scan_request.hash],
            cwd=scan_request.cwd,
            capture_output=True,
            check=True,
        )
        return True
    except subprocess.CalledProcessError as exc:
        log.error(f"Unable to git checkout: {scan_request.as_of} {scan_request.hash[:8]} -> {exc}")
        return False


def _get_repo_cache_dir(git_url: str) -> Path:
    """Return our *local* cache path for the specified git url."""
    # NB: Automatically handles XDG on Linux, AppData on Windows, etc.
    cache_base = Path(user_cache_dir("mq", "pborocz"))  # app_name, author

    # Extract user/repo from URL
    parsed = urlparse(git_url)
    path = parsed.path.strip("/").removesuffix(".git")

    repo_dir = cache_base / "repos" / path
    repo_dir.mkdir(parents=True, exist_ok=True)
    return repo_dir


def _get_commit_hashes(repo_path: Path) -> list[tuple[str, str]]:
    """Get all commit hashes in chronological order (oldest to newest)."""
    result = subprocess.run(
        ["git", "log", "--reverse", "--pretty=format:%H|%at", "origin/HEAD"],  # Unix timestamp!
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
