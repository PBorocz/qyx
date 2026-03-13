"""Define all the "core" peewee models, ie. over and above "tool"-specific storage."""

from __future__ import annotations

import logging
from datetime import datetime, UTC
from typing import TYPE_CHECKING

import peewee as pw

from .base import BaseModel
from .request import Request
from qyx.utils import dt_to_display

if TYPE_CHECKING:
    from .project import Project  # Only imported for type checking


log = logging.getLogger(__name__)


class Scan(BaseModel):
    """A 'Scan' is the execution of a particular tool at a particular time obo of a specific request."""

    id = pw.AutoField()

    request = pw.ForeignKeyField(Request, backref="scan", on_delete="CASCADE")
    as_of = pw.DateTimeField(help_text="As Of GMT/UTC datetime of the code base being analysed")
    analysis = pw.CharField(help_text="Analysis performed, e.g. cloc, cc, mi, hal, ruff etc.", null=True)
    tool = pw.CharField(help_text="Tool used, e.g. cloc, radon, ruff etc.", null=True)
    git_commit_hash = pw.CharField(help_text="Git commit/revision hash", null=True)
    git_commit_message = pw.TextField(help_text="Git message", null=True)
    timestamp = pw.DateTimeField(
        help_text="GMT/UTC datetime the scan/ingest occurred",
        default=lambda: datetime.now(UTC).replace(microsecond=0),
    )

    class Meta:
        """Define peewee meta data."""

        indexes = (
            # Uniqueness criteria
            (("request", "as_of", "analysis", "tool"), True),
            # Query optimization for filtering + sorting
            (("request", "analysis", "as_of"), False),
        )

    @classmethod
    def get_most_recent(cls, project: "Project", tool: str = None, analysis: str = None) -> "Scan" | None:
        """Find the most recent scan for the specified project, tool and analysis BY AS-OF DATE!"""
        from .request import Request

        query = Scan.select().where(Request.project == project).join(Request).order_by(Scan.as_of.desc())
        if tool:
            query = query.where(Scan.tool == tool)
        if analysis:
            query = query.where(Scan.analysis == analysis)
        if run := query.first():
            return run
        return None

    def analysis_display(self) -> str:
        """Return a nicely formatted tool + analysis."""
        if self.tool == self.analysis:
            return f"{self.tool:9s}"
        else:
            return f"{self.tool:5s}:{self.analysis:3}"

    def as_of_display(self, **kwargs) -> str:
        """Return the scan AsOf date nicely formatted in local time."""
        return dt_to_display(self.as_of, **kwargs)
