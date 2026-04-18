"""..."""

import logging
from argparse import Namespace
from types import SimpleNamespace as Sns

import peewee as pw
from playhouse.sqlite_ext import JSONField

# from peewee import fn

from qyx.constants import ViewContext as Vc
from qyx.tools._models_ import BaseModel, Scan

# from qyx.tools.common import get_loc, get_scans_for_project_dimension
# from qyx.utils import rate_of_change_percentage

log = logging.getLogger(__name__)


class Ga(BaseModel):
    """Git Analytics base model."""

    # fmt: off
    id                = pw.AutoField()
    scan              = pw.ForeignKeyField(Scan, on_delete="CASCADE")
    authorship        = JSONField(null=True)
    bug_commits       = JSONField(null=True)
    commit_frequency  = JSONField(null=True)
    emergency_commits = JSONField(null=True)
    file_churn        = JSONField(null=True)
    # fmt: on

    class Meta:
        """..."""

        table_name = "tool_ga"
        indexes = ((("scan",), True),)


def query_ga_0(args: Namespace, scan: Scan, dimension: str = None, context: Vc = Vc.TOOL_HOME) -> Sns:
    if ga_ := Ga.select().where(Ga.scan == scan).dicts().first():
        if dimension:
            return Sns(**{dimension: ga_.get(dimension)})
        else:
            return Sns(**ga_)
    return Sns()
