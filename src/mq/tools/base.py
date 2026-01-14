"""..."""

from __future__ import annotations

import logging
import types
from abc import ABC
from argparse import Namespace
from datetime import datetime, UTC
from importlib import import_module
from typing import Callable

import peewee as pw

from mq.utils import dt_to_display, parse_path_arg


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

    def get_ingest_method(self, *args, **kwargs) -> Callable:
        """Return the parse method to parse this tool's JSON output."""
        # NOTE: This implementation is the "single"-analysis tools (ruff, cloc etc.).
        # For multi-analysis tools (like radon), this method is overridden in their respective __init__.py.
        py_ingest = import_module(f"mq.tools.{self.module_name}.ingest")  # eg. .../<module>/ingest.py
        return getattr(py_ingest, "ingest")


################################################################################################
# Base Peewee Model Definitions (ie. database tables)
################################################################################################
class BaseModel(pw.Model):
    """Root of our "tree" of models."""

    class Meta:
        """Define peewee orm/table semantics."""

        database = None


class Project(BaseModel):
    """Root of result storage, a 'project' is primarily just a project "name"."""

    id = pw.AutoField()

    name = pw.CharField(
        help_text="Name of the project, used for display purposes and to match obo uniqueness.",
        unique=True,
    )

    created = pw.DateTimeField(
        help_text="GMT/UTC datetime the project was created.",
        default=lambda: datetime.now(UTC),
    )

    @classmethod
    def find_from_args(cls, args: Namespace) -> Project | None:
        """Get the project of the specified input name or path."""
        if args.name:
            name = args.name
        else:
            # No name provided...can we get the name from the path?
            (name, _, _) = parse_path_arg(args.path)

        # Can we find it?
        if project := cls.get_or_none(cls.name == name):
            return project

        return None

    @classmethod
    def create_from_args(cls, args: Namespace) -> Project:
        """Get the project of the specified input path, even if we have to insert."""
        if project := cls.find_from_args(args):
            return project

        # Nope, create a new instance...
        name = args.name if args.name else parse_path_arg(args.path)[0]
        project = cls.create(name=name)
        log.info(f"Created a new project: {name=}")
        return project


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

    arg_raw = pw.CharField(
        help_text="Project argument as entered by user, eg '.' or '../src', '/abs/path', 'https:...').",
    )

    arg_normalised = pw.CharField(
        help_text="Arg_Normalised identifier for pathing (could be file path or git repo!)",
    )

    is_git = pw.BooleanField(
        help_text="Is this a git project?",
    )

    class Meta:
        """Define peewee meta data."""

        indexes = ((("project", "timestamp"), True),)

    @classmethod
    def get_or_create(cls, args: Namespace, project: Project) -> Request:
        """Return the appropriate request instance, whether (back)filling a git history or new."""
        (name, normalised, is_git) = parse_path_arg(args.path)

        if not is_git:
            # For a NON git-based scan (ie. a directory), we create a new Request each time, easy!!
            log.debug("Creating new request this project...")
            return cls.create_from_args(project, args, normalised, is_git)

        # Otherwise, we first look for the most recent git-based Request for this project.
        request = (
            cls.select()
            .order_by(Request.timestamp.asc())
            .where(
                Request.project == project,
                Request.is_git,
            )
            .first()
        )
        if request:
            log.debug(f"Found existing git {request.id=}, using it...")
            request.timestamp = datetime.now(UTC)
            request.save()
        else:
            log.debug("No existing git request found for this project, creating a new one.")
            request = cls.create_from_args(project, args, normalised, is_git)
        return request

    @classmethod
    def create_from_args(cls, project: Project, args: Namespace, normalised: str, is_git: bool) -> Request:
        """Create a new request instance on behalf of the specified Project."""
        return cls.create(
            project=project,
            arg_raw=args.path,
            arg_normalised=normalised,
            is_git=is_git,
        )


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

    def tool_analysis_display(self) -> str:
        """Return a nicely formatted tool + analysis."""
        if self.tool == self.analysis:
            return f"{self.tool:9s}"
        else:
            return f"{self.tool:5s}:{self.analysis:3}"

    def as_of_display(self, **kwargs) -> str:
        """Return the scan AsOf date nicely formatted in local time."""
        return dt_to_display(self.as_of, **kwargs)


class BaseResultsModel(pw.Model):
    """Define an base model definition from which all the module's storage model(s) will inherit."""

    # fmt: off
    id        = pw.AutoField()
    scan      = pw.ForeignKeyField(Scan, backref="modules", on_delete="CASCADE")
    directory = pw.CharField(help_text="eg. src/mq/") # Relative to project's root!
    filename  = pw.CharField(help_text="eg. foo.py")
    # fmt: on
