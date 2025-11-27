"""..."""

from argman.argman import _ArgResult

from pcq.models import Run
from pcq.utilities.git import get_git_commit_hash


def ingest(args: _ArgResult, db):
    gch = get_git_commit_hash()
    run = Run(git_commit_hash=gch, source_dir="aSourceDir", run_module="ruff_check")
    run.save()
