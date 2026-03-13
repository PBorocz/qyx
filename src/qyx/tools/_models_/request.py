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

        if not is_git:
            # For a NON git-based scan (ie. a directory), we create a new Request each time, easy!!
            log.debug("Creating new request this project...")
            return cls.factory(project, args, normalised, is_git)

        # Otherwise, we first look for the most recent git-based Request for this project.
        request = (
            cls.select()
            .order_by(Request.id.asc())
            .where(
                Request.project == project,
                Request.is_git,
            )
            .first()
        )
        if request:
            log.debug(f"Found existing git {request.id=}, using it...")
            request.save()
        else:
            log.debug("No existing git request found for this project, creating a new one.")
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
