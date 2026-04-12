"""Wrapper to run all "git analytics" obo "Ga" tool, saving results to tmp file and return path to it."""

#
# HT: https://piechowski.io/post/git-commands-before-reading-code/ for posting these!
#
import json
import subprocess
import sys
import tempfile
from collections import Counter
from subprocess import CompletedProcess
# Note: Any of these could get "--since=1 year ago" to limit scope.


def main():
    repo_path = sys.argv[1] if len(sys.argv) > 1 else "."

    results = dict()

    # Gather various git analytics..
    # fmt: off
    results["authorship"        ] = _get_authorship(repo_path)
    results["bug_commits"       ] = _get_bug_commits(repo_path)
    results["commit_frequency"  ] = _get_commit_frequency(repo_path)
    results["emergency_commits" ] = _get_emergency_commits(repo_path)
    results["file_churn"        ] = _get_file_churn(repo_path)
    # fmt: on

    # Write the dictionary as JSON (with delete=False to keep it after closing)
    temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(results, temp_file, indent=2)
    temp_file.close()

    # Critical: We hand back the path to the temp file so the ingest
    # logic can read, parse and save the results.
    print(temp_file.name)


def _get_commit_frequency(repo_path: str) -> list[tuple[str, int]]:
    result = __subprocess(
        repo_path,
        ["git", "log", "--format=%ad", "--date=format:%Y-%m"],
    )
    commit_dates_by_month = [line for line in result.stdout.splitlines() if line.strip()]
    commits_by_month = Counter(commit_dates_by_month)
    return sorted(commits_by_month.most_common(20))  # Safe to sort here as first element is date!!


def _get_file_churn(repo_path: str) -> list[tuple[str, int]]:
    result = __subprocess(
        repo_path,
        [
            "git",
            "log",
            "--format=format:",
            "--name-only",
        ],
    )
    files = [line for line in result.stdout.splitlines() if line.strip()]
    file_counts = Counter(files)
    return file_counts.most_common(20)


def _get_authorship(repo_path: str) -> list[tuple[str, int]]:
    result = __subprocess(
        repo_path,
        [
            "git",
            "log",
            "--format='%an'",
            "--no-merges",
        ],
    )
    authors = [line for line in result.stdout.splitlines() if line.strip()]
    author_counts = Counter(authors)
    return author_counts.most_common(20)


def _get_bug_commits(repo_path: str) -> list[tuple[str, int]]:
    result = __subprocess(
        repo_path,
        [
            "git",
            "log",
            "-i",
            "-E",
            "--grep=fix|bug|broken|issue",
            "--name-only",
            "--format=",
        ],
    )
    files = [line for line in result.stdout.splitlines() if line.strip()]
    file_counts = Counter(files)
    return file_counts.most_common(20)


def _get_emergency_commits(repo_path: str) -> list[tuple[str, int]]:
    result = __subprocess(
        repo_path,
        [
            "git",
            "log",
            "--oneline",
            "-i",
            "-E",
            "--grep=revert|hotfix|emergency|rollback",
            "--format=%ad",
            "--date=format:%Y-%m",
        ],
    )
    commits = [line for line in result.stdout.splitlines() if line.strip()]
    commit_counts = Counter(commits)
    return commit_counts.most_common(20)


def __subprocess(repo_path: str, cmd_list: list[str]) -> CompletedProcess[str]:
    return subprocess.run(cmd_list, cwd=repo_path, capture_output=True, text=True, check=True)


if __name__ == "__main__":
    main()
