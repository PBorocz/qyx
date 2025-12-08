"""..."""

from __future__ import annotations

import zoneinfo
from datetime import datetime

import peewee as pw


class Project(pw.Model):
    """..."""

    source_dir = pw.CharField(help_text="Pointer to respective project's root directory")

    @classmethod
    def get_or_insert(cls, source_dir: str) -> Project:
        """Get the project at the specified source directory, even if we have to insert."""
        try:
            project = Project.get(Project.source_dir == source_dir)
        except pw.DoesNotExist:
            project = Project(source_dir=source_dir)
        project.save()
        return project


class Run(pw.Model):
    """..."""

    # fmt: off
    project_id      = pw.ForeignKeyField(Project, backref="Runs")
    timestamp       = pw.DateTimeField() # "GMT/UTC datetime the ingest occurred"
    git_commit_hash = pw.CharField()     # ID from respective sport's site")
    module          = pw.CharField()     # Module gathered for, e.g. ruff, cloc, radon etc.
    # fmt: on

    @property
    def timestamp_local(self) -> datetime:
        """..."""
        return self.timestamp.replace(tzinfo=zoneinfo.ZoneInfo("UTC")).astimezone()
