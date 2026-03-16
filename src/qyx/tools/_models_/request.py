"""Define all the "core" peewee models, ie. over and above "tool"-specific storage."""

import logging
from argparse import Namespace

import peewee as pw

from .base import BaseModel
from .project import Project
from qyx.utils import parse_path_arg


log = logging.getLogger(__name__)


class Request(BaseModel):
    """A 'Request' captures the user desire to perform an analysis."""

    id = pw.AutoField()
    project = pw.ForeignKeyField(Project, backref="request", on_delete="CASCADE")
    arg_raw = pw.CharField(help_text="Project arg from user, eg '.' or '../src', '/abs/path', 'https:...').")
    arg_normalised = pw.CharField(help_text="Arg_Normalised identifier for pathing (could be file path or git repo!)")
    is_git = pw.BooleanField(help_text="Is this a git project?")

    class Meta:
        """Define peewee meta data."""

        indexes = ((("project", "arg_normalised", "is_git"), True),)

    @classmethod
    def get_or_create(cls, args: Namespace, project: "Project") -> "Request":
        """Return the appropriate request instance, whether (back)filling a git history or new."""
        (name, normalised, is_git) = parse_path_arg(args.path)

        # Look for the most recent Request for this project based on whether or not we're using git.
        request = Request.get(
            Request.project == project,
            Request.arg_normalised == normalised,
            Request.is_git == is_git,
        )
        if not request:
            log.debug("No existing request found for this project, creating a new one.")
            request = cls.factory(project, args, normalised, is_git)
        else:
            log.debug(f"Found existing request {request.id=}, using it...")
        return request

    @classmethod
    def factory(cls, project: Project, args: Namespace, normalised: str, is_git: bool) -> "Request":
        """Create a new request instance on behalf of the specified Project."""
        return cls.create(
            project=project,
            arg_raw=args.path,
            arg_normalised=normalised,
            is_git=is_git,
        )
