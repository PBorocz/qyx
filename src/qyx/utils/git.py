"""..."""

import logging
import re
import subprocess
from argparse import Namespace
from datetime import datetime, timezone
from pathlib import Path
from platformdirs import user_cache_dir
from types import SimpleNamespace as Sns
from urllib.parse import urlparse

log = logging.getLogger(__name__)


def get_git_commits(git_repo: str) -> tuple[Path, list[Sns]]:
    """Setup the git repository (cloning if necessary) and get the list of commit revisions."""
    repo_path = _get_repo_cache_dir(git_repo)

    # Do we need to clone "anew" or can we use an refresh to an existing cached repository?
    if repo_path.exists() and (repo_path / ".git").exists():
        # Yep, we still have it, refresh it!
        log.info(f"Updating existing repo at {repo_path}")
        subprocess.run(
            ["git", "fetch", "origin"],
            cwd=repo_path,
            check=True,
        )
    else:
        # Don't have it yet locally, clone it (but only the "default" branch, we don't care about others)
        log.info(f"Cloning '{git_repo}' into {repo_path}...")
        subprocess.run(
            ["git", "clone", "--single-branch", git_repo, str(repo_path)],
            check=True,
            capture_output=True,
        )

    # Given the repo, find *all* commit revisions that have occurred
    commits: list[Sns] = _get_commits(repo_path)
    log.debug(f"{repo_path} has {len(commits):,d} actual commits")

    # Apply date-based filtering before we return (future enhancement to support other algorithms here?)
    commits = _filter_commits_by_daily_sampling(commits)
    log.debug(f"{repo_path} has {len(commits):,d} commits after sampling")

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


def git_goto_head(git_repo: str) -> bool:
    """Checkout HEAD in the git repository."""
    repo_path = _get_repo_cache_dir(git_repo)
    try:
        log.debug(f"Checkout out HEAD: {git_repo=} {repo_path=}")
        result = subprocess.run(
            ["git", "checkout", "--force", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        if result.stderr:
            log.debug(f"git checkout output: {result.stderr.strip()}")
        return True
    except subprocess.CalledProcessError as exc:
        log.error(f"Unable to git checkout HEAD: -> {exc}")
        return False


def _get_repo_cache_dir(git_url: str) -> Path:
    """Return our *local* cache path for the specified git url."""
    # NB: Automatically handles XDG on Linux, AppData on Windows, etc.
    # On MacOS for example -> ~/Library/Caches/qyx/repos/...
    cache_base = Path(user_cache_dir("qyx"), "repos")

    # Use github user & repo name from URL to get cache directory.
    owner, repo = _parse_github_url(git_url)
    repo_dir = cache_base / owner / repo
    repo_dir.mkdir(parents=True, exist_ok=True)
    return repo_dir


def _get_commits(repo_path: Path) -> list[Sns]:
    """Get all commit hashes in reverse chronological order, ie. newest to oldest."""
    result = subprocess.run(
        ["git", "log", "--pretty=format:%H|%at|%s", "origin/HEAD"],  # Unix timestamp!
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=True,
    )
    commits = []
    for idx, line in enumerate(result.stdout.strip().split("\n")):
        hash_val, s_date, message = line.split("|", maxsplit=2)
        utc_date = datetime.fromtimestamp(int(s_date), tz=timezone.utc)
        commits.append(
            Sns(
                hash_val=hash_val,
                utc_date=utc_date,
                message=message,
                latest=(idx == 0),
            ),
        )
    return commits


def _filter_commits_by_daily_sampling(commits: list[Sns]) -> list[Sns]:
    """Sample git commits to take only the latest commit per calendar day, returning oldest to newest."""
    # This algorithm works best for my style of development, specifically:
    # - A flurry of activity over a few days (many intraday commits), followed by
    # - Long periods of sporadic commits.
    # We don't need to analyse each intraday commit but still want the sporadic ones,
    # thus, below we take the *last* commit for each calendar day that has a commit.
    if not commits:
        return []

    # Sort newest to oldest so we process each day in reverse order (ie. by
    # newest first, we'll take the commmit that occurred *last* in the day)
    sorted_commits = sorted(commits, key=lambda c: c.utc_date, reverse=True)

    # Now, take the *last* commit of each git commit "day".
    seen_days = set()
    sampled: list[Sns] = []
    for commit in sorted_commits:
        day = commit.utc_date.date()
        if day not in seen_days:
            sampled.append(commit)
            seen_days.add(day)

    # However, return the commit in oldest -> newest order to:
    # - Leave the repo in "HEAD" state.
    # - Take advantage of git's easier processing for rolling "forwards" in time.
    return sorted(sampled, key=lambda commit: commit.utc_date)


def _parse_github_url(url: str) -> tuple[str, str]:
    """Parse GitHub URL into (owner, repo) [thanks Claude for the re's]."""
    url = url.strip()

    # SSH: git@github.com:owner/repo.git
    if match := re.match(r"git@github\.com:([^/]+)/(.+?)(?:\.git)?$", url):
        return match.group(1).lower(), match.group(2).lower()

    # HTTPS: add protocol if missing
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)
    path_parts = parsed.path.strip("/").split("/")

    if len(path_parts) >= 2:
        owner = path_parts[0].lower()
        repo = path_parts[1].removesuffix(".git").lower()
        return owner, repo

    raise ValueError(f"Cannot parse GitHub URL: {url}")
