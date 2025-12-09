"""..."""

from __future__ import annotations

import zoneinfo
from datetime import datetime
from pathlib import Path

import peewee as pw


class Project(pw.Model):
    """..."""

    source_dir = pw.CharField(help_text="Pointer to respective project's root directory")

    @classmethod
    def get_or_insert(cls, source_dir: str) -> Project:
        """Get the project at the specified source directory, even if we have to insert."""
        path_source_dir = Path(source_dir).resolve()
        try:
            project = Project.get(Project.source_dir == path_source_dir)
        except pw.DoesNotExist:
            project = Project(source_dir=path_source_dir)
        project.save()
        return project


class Run(pw.Model):
    """..."""

    # fmt: off
    project_id      = pw.ForeignKeyField(Project, backref="Runs")
    timestamp       = pw.DateTimeField() # "GMT/UTC datetime the ingest occurred"
    git_commit_hash = pw.CharField()     # ID from respective sport's site")
    module          = pw.CharField()     # Module gathered for, e.g. ruff, cloc, radon etc.
    sub_module      = pw.CharField()     # Optional sub-module, e.g. cc or raw obo radon.
    # fmt: on

    @property
    def timestamp_local(self) -> datetime:
        """..."""
        return self.timestamp.replace(tzinfo=zoneinfo.ZoneInfo("UTC")).astimezone()
