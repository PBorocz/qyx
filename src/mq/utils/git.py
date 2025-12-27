"""..."""

import subprocess
from urllib.parse import urlparse


def get_git_commit_hash() -> str:
    try:
        result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "unknown"  # Not in git repo or git not available


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
