"""..."""

from __future__ import annotations

import zoneinfo
from datetime import datetime
from pathlib import Path

import peewee as pw


class BaseModel(pw.Model):
    """Root of our "tree" of models."""

    class Meta:
        """Define peewee orm/table semantics."""

        database = None


class Project(BaseModel):
    """Root of result storage, a 'project' is essentially just a project root directory."""

    id = pw.AutoField()  # Explicitly add for clarity
    source_dir = pw.CharField(
        help_text="Pointer to respective project's root directory",
        null=False,
        unique=True,
    )

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


class Run(BaseModel):
    """A 'Run' is the execution of a particular module at a particular time for a project."""

    # fmt: off
    id              = pw.AutoField()      # Explicitly add for clarity
    project_id      = pw.ForeignKeyField(Project, null=False, backref="project")
    timestamp       = pw.DateTimeField(help_text="GMT/UTC datetime the ingest occurred", null=False)
    module          = pw.CharField(help_text="Module gathered for, e.g. ruff, cloc, radon etc.", null=False)
    sub_module      = pw.CharField(help_text="Optional sub-module, e.g. cc or raw obo radon.")
    git_commit_hash = pw.CharField(help_text="ID from respective sport's site")
    # fmt: on

    class Meta:
        """Define peewee meta data."""

        indexes = ((("project_id", "timestamp", "module", "sub_module"), True),)

    @property
    def timestamp_local(self) -> datetime:
        """..."""
        return self.timestamp.replace(tzinfo=zoneinfo.ZoneInfo("UTC")).astimezone()


class BaseModuleModel(pw.Model):
    """Define an base model definition from which all the module's storage model(s) will inherit."""

    # fmt: off
    id       = pw.AutoField()      # Explicitly add for clarity
    run_id   = pw.ForeignKeyField(Run, backref="run", null=False)
    dir      = pw.CharField(help="Relative directory of file under evaluation.", null=False)
    filename = pw.CharField(help="Name of file under evaluation.", null=False)
    # fmt: on

    @classmethod
    def initialize_for_database(cls, database):
        """Define dynamic table creation without dedicated SQL script(s)."""
        cls._meta.database = database
        cls.create_table(safe=True)
