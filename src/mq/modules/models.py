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
    """Root of result storage, a 'project' is essentially just a project root directory.

    We store this two ways:
    - As the user entered it (relative or absolute), ie. both are possible:
      1. "."
      2. /user/me/development/projects/myproject

    - As the absolute (ie. resolved) path, for the 2 cases above, this might be:
      1. /user/me/development/projects/myproject
      2. /user/me/development/projects/myproject

    We use the relative path for display purposes to match user's initial entry
    while the absolute
    """

    id = pw.AutoField()  # (explicitly add for clarity)
    source_dir_relative = pw.CharField(
        help_text="Path to respective project's root directory as entered by user.",
    )
    source_dir_absolute = pw.CharField(
        help_text="Path to respective project's root directory, resolved to absolute path",
        unique=True,
    )

    @classmethod
    def get_or_insert(cls, arg_source_dir: str) -> Project:
        """Get the project at the specified source directory, even if we have to insert."""
        path_source_dir_absolute = Path(arg_source_dir).resolve()
        try:
            project = Project.get(Project.source_dir_absolute == path_source_dir_absolute)
        except pw.DoesNotExist:
            project = Project(
                source_dir_relative=arg_source_dir,
                source_dir_absolute=path_source_dir_absolute,
            )
            project.save()
        return project


class Run(BaseModel):
    """A 'Run' is the execution of a particular module at a particular time for a project."""

    # fmt: off
    id              = pw.AutoField()      # Explicitly add for clarity
    project_id      = pw.ForeignKeyField(Project, backref="project")
    timestamp       = pw.DateTimeField(help_text="GMT/UTC datetime the ingest occurred", default=datetime.utcnow)
    module          = pw.CharField(help_text="Module gathered for, e.g. ruff, cloc, radon etc.")
    sub_module      = pw.CharField(help_text="Optional sub-module, e.g. cc or raw obo radon.", null=True)
    git_commit_hash = pw.CharField(help_text="ID from respective sport's site", null=True)
    # fmt: on

    class Meta:
        """Define peewee meta data."""

        indexes = ((("project_id", "timestamp", "module", "sub_module"), True),)

    @property
    def timestamp_display(self) -> str:
        """..."""
        dt_local: datetime = self.timestamp.replace(tzinfo=zoneinfo.ZoneInfo("UTC")).astimezone()
        return dt_local.strftime("%Y-%m-%d %H:%M")

    @classmethod
    def get_most_recent(cls, project: Project, module: str) -> Run | None:
        """Find the most recent run for the specified project and module."""
        run = (
            Run.select()
            .order_by(Run.timestamp.desc())
            .where(Run.project_id == project.id, Run.module == module)
            .first()
        )
        if run:
            return run
        return None


class BaseModuleModel(pw.Model):
    """Define an base model definition from which all the module's storage model(s) will inherit."""

    # fmt: off
    id       = pw.AutoField()      # Explicitly add for clarity
    run_id   = pw.ForeignKeyField(Run, backref="run")
    filename = pw.CharField(help_text="Name of file under evaluation.")
    dir      = pw.CharField(help_text="Relative directory of file under evaluation.")
    # fmt: on
