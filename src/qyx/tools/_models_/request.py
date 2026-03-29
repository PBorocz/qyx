"""Define all the "core" peewee models, ie. over and above "tool"-specific storage."""

import logging
from argparse import Namespace

import peewee as pw
from peewee import fn

from .base import BaseModel
from .project import Project
from qyx.utils import parse_path_arg


log = logging.getLogger(__name__)


class Request(BaseModel):
    """A 'Request' captures the user desire to perform an ingestion for a particular project."""

    id = pw.AutoField()

    project = pw.ForeignKeyField(Project, backref="request", on_delete="CASCADE")

    # Project arg from user, eg '.' or '../src', '/abs/path', 'https:...').
    arg_raw = pw.CharField()

    # Arg_Normalised identifier for pathing (could be file path or git repo!)
    arg_normalised = pw.CharField()

    # Is this a git project?
    is_git = pw.BooleanField()

    class Meta:
        """Define peewee meta data."""

        indexes = ((("project", "arg_normalised", "is_git"), True),)

    @classmethod
    def get_or_create(cls, args: Namespace, project: "Project") -> "Request":
        """Return the appropriate request instance, whether (back)filling a git history or new."""
        (name, normalised, is_git) = parse_path_arg(args.path)

        # Look for the most recent Request for this project based on whether or not we're using git.
        try:
            request = Request.get(
                Request.project == project,
                fn.LOWER(Request.arg_normalised) == normalised.lower(),
                Request.is_git == is_git,
            )
            log.debug(f"Found existing request {request.id=}, using it...")
        except Request.DoesNotExist:
            log.debug("No existing request found for this project, creating a new one.")
            request = cls.factory(project, args, normalised, is_git)

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
