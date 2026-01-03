"""..."""

from __future__ import annotations

import logging
import types
from abc import ABC
from argparse import Namespace
from datetime import datetime, UTC
from pathlib import Path

import peewee as pw

from mq.utils import detect_project_name, timestamp_display


log = logging.getLogger(__name__)


################################################################################################
class AbstractModuleConfiguration(ABC):
    """Defines all the semantics of a code quality tool (aka module) supported by this package."""

    def __init__(
        self,
        module_name: str,
        analyses: tuple[str],
        models: tuple[BaseModel],
        **kwargs,
    ) -> "AbstractModuleConfiguration":
        """..."""
        # Name of directory implementing the tool, e.g. "ruff" obo ../src/mq/tools/ruff
        self.module_name: str = module_name

        # Peewee storage models used by this tool.
        self.models: tuple[BaseModel] = models

        # Analyses support by the tool (even if 1 for stuff like cloc and ruff)
        self.analyses: tuple[str] = analyses

        # Are Results "required" for a Scan to be valid? (usually yes)
        self.results_required = True

        # Handle to the mq/tools/{module_name}/ module itself!
        self.py_module: types.ModuleType = None

        # Save any other values sent in...
        for attr, value in kwargs.items():
            setattr(self, attr, value)

    def get_ingest_command(self, *args, **kwargs):
        """Return the command sent to subprocess to directly perform a CLOC operation."""
        raise NotImplementedError("Sorry, this method needs to be implemented by an inherited class!")

    def get_ingest_method(self, *args, **kwargs):
        """Return the parse method to parse this Radon sub_module's JSON output."""
        raise NotImplementedError("Sorry, this method needs to be implemented by an inherited class!")


################################################################################################
# Base Peewee Model Definitions (ie. database tables)
################################################################################################
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
        backref="requests",
        on_delete="CASCADE",
    )
    timestamp = pw.DateTimeField(
        help_text="GMT/UTC datetime the ingest occurred",
        default=lambda: datetime.now(UTC),
    )
    git_repo = pw.CharField(
        help_text="If the source of this request was a git, what was it?",
        null=True,
    )

    class Meta:
        """Define peewee meta data."""

        indexes = ((("project", "timestamp"), True),)

    @classmethod
    def create_from_args(cls, args: Namespace, project: Project) -> Request:
        """Create a new request instance taking care to set the input based on CLI args."""
        return cls.create(project=project, git_repo=args.git)

    @classmethod
    def get_or_create(cls, args: Namespace, project: Project) -> Request:
        """Return the appropriate request instance, whether (back)filling a git history or new."""
        if not args.git:
            # For a NON git-based scan (ie. a directory), we create a new Request each time...
            return cls.create_from_args(args, project)

        # Otherwise, we first look for the most recent git-based Request for this project.
        request = (
            cls.select()
            .order_by(Request.timestamp.asc())
            .where(
                Request.project == project,
                Request.git_repo.is_null(False),
            )
            .first()
        )
        if request:
            log.debug(f"Found existing git {request.id=}, using it...")
            request.timestamp = datetime.now(UTC)
            request.save()
        else:
            log.debug("No existing git request found for this project, creating a new one.")
            request = cls.create_from_args(args, project)
        return request

    # NOTE: IS THIS USED ANYMORE ANYWHERE?
    # @classmethod
    # def get_most_recent(cls, project: Project) -> Request | None:
    #     """Find the most recent request for he specified project."""
    #     query = Request.select().order_by(Request.timestamp.desc()).where(Request.project == project.id)
    #     if run := query.first():
    #         return run
    #     return None

    def from_git(self) -> bool:
        """Return true if this request is based on a git repository history."""
        return self.git_repo is not None

    def timestamp_display(self, full: bool = False) -> str:
        """..."""
        return timestamp_display(self.timestamp)


class Scan(BaseModel):
    """A 'Scan' is the execution of a particular tool at a particular time obo of a specific request."""

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
    analysis = pw.CharField(
        help_text="Analysis performed, e.g. cloc, cc, mi, hal, ruff etc.",
        null=True,
    )
    tool = pw.CharField(
        help_text="Tool used, e.g. cloc, radon, ruff etc.",
        null=True,
    )
    # cwd = pw.CharField(
    #     help_text="Directory for tool execuction (ie. /tmp/... for git or /users/dev/project",
    #     null=True,
    # )
    git_commit_hash = pw.CharField(
        help_text="ID from respective sport's site",
        null=True,
    )
    timestamp = pw.DateTimeField(
        help_text="GMT/UTC datetime the scan occurred",
        default=lambda: datetime.now(UTC),
    )

    class Meta:
        """Define peewee meta data."""

        indexes = ((("request", "as_of", "analysis", "tool"), True),)

    @classmethod
    def get_most_recent(cls, project: Project, tool: str = None, analysis: str = None) -> Scan | None:
        """Find the most recent scan for the specified project, tool and analysis BY AS-OF DATE!"""
        query = Scan.select().where(Request.project == project).join(Request).order_by(Scan.as_of.desc())
        if tool:
            query = query.where(Scan.tool == tool)
        if analysis:
            query = query.where(Scan.analysis == analysis)
        if run := query.first():
            return run
        return None

    def as_of_display(self, full: bool = False) -> str:
        """..."""
        return timestamp_display(self.as_of)

    def tool_analysis_display(self) -> str:
        """Return a nicely formatted tool + analysis."""
        if self.tool == self.analysis:
            return f"{self.tool:9s}"
        else:
            return f"{self.tool:5s}:{self.analysis:3}"


class BaseResultsModel(pw.Model):
    """Define an base model definition from which all the module's storage model(s) will inherit."""

    # fmt: off
    id        = pw.AutoField()
    scan      = pw.ForeignKeyField(Scan, backref="modules", on_delete="CASCADE")
    directory = pw.CharField(help_text="eg. src/mq/")
    filename  = pw.CharField(help_text="eg. foo.py")
    # fmt: on
