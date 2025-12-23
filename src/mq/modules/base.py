"""..."""

from __future__ import annotations

import zoneinfo
from datetime import datetime
from pathlib import Path

import peewee as pw

from mq.utils import detect_project_name


class BaseModel(pw.Model):
    """Root of our "tree" of models."""

    class Meta:
        """Define peewee orm/table semantics."""

        database = None


class Project(BaseModel):
    """Root of result storage, a 'project' is essentially just a project root directory.

    We store this 3 ways:
    - As the user entered it (relative or absolute), ie. both are possible:
      1. "."
      2. /user/me/development/projects/myproject

    - As the absolute (ie. resolved) path, for the 2 cases above, this might be:
      1. /user/me/development/projects/myproject
      2. /user/me/development/projects/myproject

    - As a "display" name for use in reporting
      (this uses logic at creation time)
    """

    id = pw.AutoField()
    path_input = pw.CharField(
        help_text="Path as entered by user (e.g., '.', '../src', '/abs/path').",
    )
    path_absolute = pw.CharField(
        help_text="Resolved absolute path to project root directory.",
        unique=True,
    )
    path_display = pw.CharField(
        help_text="Human-friendly display name for reports and UI.",
    )
    created = pw.DateTimeField(
        help_text="GMT/UTC datetime the project was created.",
        default=datetime.utcnow,
    )

    @classmethod
    def get_or_insert_raw(cls, path_input: str, path_absolute: str, display: str) -> Project:
        """Get the project of the specified input path, even if we have to insert."""
        try:
            project = cls.get(cls.path_input == path_input)
        except pw.DoesNotExist:
            project = cls.create(
                path_input=path_input,
                path_absolute=path_absolute,
                path_display=display,
            )
        return project

    @classmethod
    def get_or_insert_relative(cls, arg_input_dir: str) -> Project:
        """Get the project at the specified source directory, even if we have to insert."""
        path_absolute = str(Path(arg_input_dir).resolve())
        path_display = _generate_display_name(path_absolute)
        return cls.get_or_insert_raw(arg_input_dir, path_absolute, path_display)
        # try:
        #     project = cls.get(cls.path_absolute == path_absolute)
        # except pw.DoesNotExist:
        #     path_display = generate_display_name(path_absolute)
        #     project = cls.create(
        #         path_input=arg_input_dir,
        #         path_absolute=path_absolute,
        #         path_display=path_display,
        #     )
        # return project


def _generate_display_name(path_absolute: str) -> str:
    """Generate a human-friendly display name for the project."""
    # Try project name from config files
    if project_name := detect_project_name(path_absolute):
        return project_name

    # Use relative path if shorter and not too many levels up
    try:
        abs_path = Path(path_absolute)
        cwd = Path.cwd()
        rel_path = abs_path.relative_to(cwd)

        # Use relative if reasonable length and not too nested
        if len(str(rel_path)) < len(str(abs_path)) and len(rel_path.parts) <= 3:
            return str(rel_path)
    except ValueError:
        # abs_path is not relative to cwd
        pass

    # Fall back to directory name
    return Path(path_absolute).name


class Run(BaseModel):
    """A 'Run' is the execution of a particular module at a particular time for a project."""

    # fmt: off
    id              = pw.AutoField()
    project         = pw.ForeignKeyField(Project, backref="runs", on_delete="CASCADE")
    timestamp       = pw.DateTimeField(help_text="GMT/UTC datetime the ingest occurred", default=datetime.utcnow)
    module          = pw.CharField(help_text="Module gathered for, e.g. ruff, cloc, radon etc.")
    sub_module      = pw.CharField(help_text="Optional sub-module, e.g. cc or raw obo radon.", null=True)
    git_commit_hash = pw.CharField(help_text="ID from respective sport's site", null=True)
    # fmt: on

    class Meta:
        """Define peewee meta data."""

        indexes = ((("project", "timestamp", "module", "sub_module"), True),)

    @property
    def timestamp_display(self) -> str:
        """..."""
        dt_local: datetime = self.timestamp.replace(tzinfo=zoneinfo.ZoneInfo("UTC")).astimezone()
        format = "%H:%M%p" if dt_local.date() == datetime.now().date() else "%Y-%m-%d %H:%M%p"
        return dt_local.strftime(format)

    @classmethod
    def get_most_recent(cls, project: Project, module: str, sub_module: str = None) -> Run | None:
        """Find the most recent run for the specified project and module (or sub_module)."""
        query = Run.select().order_by(Run.timestamp.desc()).where(Run.project == project.id, Run.module == module)
        if sub_module:
            query = query.where(Run.sub_module == sub_module)
        if run := query.first():
            return run
        return None


class BaseModuleModel(pw.Model):
    """Define an base model definition from which all the module's storage model(s) will inherit."""

    # fmt: off
    id       = pw.AutoField()
    run      = pw.ForeignKeyField(Run, backref="modules", on_delete="CASCADE")
    filename = pw.CharField(help_text="Name of file under evaluation.")
    dir      = pw.CharField(help_text="Relative directory of file under evaluation.")
    # fmt: on
