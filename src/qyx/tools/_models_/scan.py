"""Define all the "core" peewee models, ie. over and above "tool"-specific storage."""

from __future__ import annotations

import logging
from datetime import datetime, UTC
from typing import TYPE_CHECKING

import peewee as pw
from playhouse.sqlite_ext import JSONField

from .base import BaseModel
from .request import Request
from qyx.utils import dt_to_display

if TYPE_CHECKING:
    from .project import Project  # Only imported for type checking


log = logging.getLogger(__name__)


class Scan(BaseModel):
    """A 'Scan' is the execution of a particular tool at a particular time obo of a specific request."""

    id = pw.AutoField()

    # What request is this Scan on behalf of?
    request = pw.ForeignKeyField(Request, backref="scan", on_delete="CASCADE")

    # As Of GMT/UTC datetime of the code base being analysed.
    as_of = pw.DateTimeField()

    # Tool used, e.g. cloc, radon, ruff etc."
    tool = pw.CharField()

    # Dimension ingested.
    # For tools with a single dimension, this will default to tool.name (e.g. cloc, ruff, ty etc.)
    # For tools with multiple *reporting* dimensions but that we ingest once, this will also be the tool name (eg. scc)
    # For tools that we ingest *BY DIMENSION*, this will be the "ingest" dimension (e.g. raw, hal, cc obo radon)
    ingest_dimension = pw.CharField()

    # Git commit/revision hash (only available when iterating over git revisions, not from file system)
    git_commit_hash = pw.CharField(null=True)

    # Git message associated with the commit/revision hash (ditto from above)
    git_commit_message = pw.TextField(null=True)

    # GMT/UTC datetime the scan/ingest occurred"
    timestamp = pw.DateTimeField(default=lambda: datetime.now(UTC).replace(microsecond=0))

    # Tool specific aggregate summary (total, overall metrics etc.)
    summary = JSONField(null=True)  # Not meant to be null, only that we don't have this on create.

    class Meta:
        """Define peewee meta data."""

        indexes = (
            # Uniqueness criteria
            (("request", "as_of", "tool", "ingest_dimension"), True),
            # Query optimization for filtering + sorting
            (("request", "as_of"), False),
        )

    @classmethod
    def get_latest(cls, project: "Project", tool: str, ingest_dimension: str = None) -> "Scan" | None:
        """Find the most recent scan for the specified project, tool and dimension BY AS-OF DATE!"""
        from .request import Request  # Circular import...arghhh

        query = (
            Scan.select()
            .where(
                Request.project == project,
                Scan.tool == tool,
            )
            .join(Request)
            .order_by(Scan.as_of.desc())
        )
        if ingest_dimension:
            query = query.where(Scan.ingest_dimension == ingest_dimension)

        return query.first()

    def as_of_display(self, **kwargs) -> str:
        """Return the scan AsOf date nicely formatted in local time."""
        return dt_to_display(self.as_of, **kwargs)

    def tool_dimension_display(self) -> str:
        """Return a nicely formatted tool + cli_option."""
        if self.tool != self.ingest_dimension:
            return f"{self.tool:5s}:{self.ingest_dimension:3}"
        else:
            return f"{self.tool:9s}"
