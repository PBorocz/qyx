"""Define all the "core" peewee models, ie. over and above "tool"-specific storage."""

from __future__ import annotations

import logging
from argparse import Namespace
from datetime import datetime, UTC
from typing import Iterator

import peewee as pw

from .base import BaseModel
from qyx.constants import ALL_ITEMS
from qyx.utils import parse_path_arg


log = logging.getLogger(__name__)


class Project(BaseModel):
    """Root of result storage, a 'project' is primarily just a project "name"."""

    id = pw.AutoField()

    name = pw.CharField(
        help_text="Name of the project, used for display purposes and to match obo uniqueness.",
        unique=True,
    )

    created = pw.DateTimeField(
        help_text="GMT/UTC datetime the project was created.",
        default=lambda: datetime.now(UTC).replace(microsecond=0),
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
    def iter_from_args(cls, args: Namespace) -> Iterator[Project]:
        """Iterate over all projects based on args.name."""
        if args.name == ALL_ITEMS:
            for project in cls:
                yield project
        else:
            yield cls.find_from_args(args)

    @classmethod
    def factory(cls, args: Namespace) -> Project:
        """Get the project of the specified input path, even if we have to insert."""
        if project := cls.find_from_args(args):
            return project

        # Nope, create a new instance...
        name = args.name if args.name else parse_path_arg(args.path)[0]
        project = cls.create(name=name)
        log.info(f"Created a new project: {name=}")
        return project
