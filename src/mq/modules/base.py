"""..."""

from __future__ import annotations

import logging
from argparse import Namespace
from datetime import datetime, UTC
from pathlib import Path

import peewee as pw
from peewee import Check

from mq.utils import detect_project_name, timestamp_display


log = logging.getLogger(__name__)


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

    name = pw.CharField(
        help_text="Descriptive name of the project, either as assigned by the user or calculated.",
    )
    input_path = pw.CharField(
        help_text="Path as entered by user, eg '.' or '../src', '/abs/path').",
        null=True,
    )
    input_git_url = pw.CharField(
        help_text="Github repo url as entered by user, eg., 'https://github.com/foo/bar'",
        null=True,
    )
    path_absolute = pw.CharField(
        help_text="Resolved absolute path to project root directory (only available for input_path)",
        unique=True,
        null=True,
    )
    created = pw.DateTimeField(
        help_text="GMT/UTC datetime the project was created.",
        default=lambda: datetime.now(UTC),
    )

    class Meta:
        """Define peewee meta data."""

        indexes = ((("name",), True),)

    @classmethod
    def get_by_identifier(cls, arg_input: str) -> Project | None:
        """Get the project using name or either input definition in Priority order!."""
        for field in [cls.name, cls.input_path, cls.input_git_url]:
            instance = cls.get_or_none(field == arg_input)
            if instance:
                return instance
        return None

    @classmethod
    def create_from_args(cls, args: Namespace) -> Project:
        """Get the project of the specified input path, even if we have to insert."""
        if project := cls.get_by_identifier(args.project):
            return project

        name = detect_project_name(args.project)
        if args.git:
            instance = cls.create(name=name, input_git_url=args.project)
            msg = "Created a new project obo Git url.."
        else:
            path_absolute = str(Path(args.project).resolve())
            msg = "Created a new project obo input path.."
            instance = cls.create(name=name, input_path=args.project, path_absolute=path_absolute)
        log.debug(msg)
        return instance


class Request(BaseModel):
    """A 'Request' captures the user desire to perform an analysis."""

    id = pw.AutoField()
    project = pw.ForeignKeyField(
        Project,
        backref="runs",
        on_delete="CASCADE",
    )
    scan_source = pw.CharField(
        help_text="Was the source of this request a git url or a directory path??",
        null=False,
    )
    timestamp = pw.DateTimeField(
        help_text="GMT/UTC datetime the ingest occurred",
        default=lambda: datetime.now(UTC),
    )

    class Meta:
        """Define peewee meta data."""

        constraints = [Check("scan_source IN ('path', 'git')")]

    @classmethod
    def create_from_args(cls, args: Namespace, project: Project) -> Request:
        """Create a new request instance taking care to set the input based on CLI args."""
        scan_source = "git" if args.git else "path"
        return Request.create(project=project, scan_source=scan_source)

    @classmethod
    def get_most_recent(cls, project: Project, module: str, sub_module: str = None) -> Request | None:
        """Find the most recent run for the specified project and module (or sub_module)."""
        query = (
            Request.select()
            .order_by(Request.timestamp.desc())
            .where(Request.project == project.id, Request.module == module)
        )
        if sub_module:
            query = query.where(Request.sub_module == sub_module)
        if run := query.first():
            return run
        return None

    def timestamp_display(self, full: bool = False) -> str:
        """..."""
        return timestamp_display(self.timestamp)


class Scan(BaseModel):
    """A 'Scan' is the execution of a particular module at a particular time for a project."""

    id = pw.AutoField()
    request = pw.ForeignKeyField(
        Request,
        backref="scans",
        on_delete="CASCADE",
    )
    as_of = pw.DateTimeField(
        help_text="As Of GMT/UTC datetime of the code base being analysed",
        default=lambda: datetime.now(UTC),
    )
    module = pw.CharField(
        help_text="Module gathered for, e.g. ruff, cloc, radon etc.",
    )
    sub_module = pw.CharField(
        help_text="Optional sub-module, e.g. cc or raw obo radon.",
        null=True,
    )
    git_commit_hash = pw.CharField(
        help_text="ID from respective sport's site",
        null=True,
    )

    class Meta:
        """Define peewee meta data."""

        indexes = ((("request", "as_of", "module", "sub_module"), True),)

    @classmethod
    def get_most_recent(cls, request: Request, module: str, sub_module: str = None) -> Scan | None:
        """Find the most recent run for the specified project and module (or sub_module)."""
        query = Scan.select().order_by(Scan.as_of.desc()).where(Scan.request == request, Scan.module == module)
        if sub_module:
            query = query.where(Scan.sub_module == sub_module)
        if run := query.first():
            return run
        return None

    def as_of_display(self, full: bool = False) -> str:
        """..."""
        return timestamp_display(self.as_of)


class BaseModuleModel(pw.Model):
    """Define an base model definition from which all the module's storage model(s) will inherit."""

    # fmt: off
    id       = pw.AutoField()
    scan     = pw.ForeignKeyField(Scan, backref="modules", on_delete="CASCADE")
    filename = pw.CharField(help_text="Name of file under evaluation.")
    dir      = pw.CharField(help_text="Relative directory of file under evaluation.")
    # fmt: on
