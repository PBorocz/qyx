"""..."""

import logging
from argparse import Namespace
from collections import defaultdict
from types import SimpleNamespace as Sns

from peewee import AutoField, BooleanField, CharField, FloatField, IntegerField, ForeignKeyField

from qyx.constants import ViewContext as Vc
from qyx.tools.base import BaseModel, Scan
from qyx.utils.caching import query_cache


log = logging.getLogger(__name__)


class Scc(BaseModel):
    """Scc language summary."""

    # fmt: off
    id                  = AutoField()
    scan                = ForeignKeyField(Scan, on_delete="CASCADE")
    name                = CharField()
    bytes               = IntegerField()
    code_bytes          = IntegerField()
    lines               = IntegerField()
    code                = IntegerField()
    comment             = IntegerField()
    blank               = IntegerField()
    complexity          = IntegerField()
    count               = IntegerField()
    weighted_complexity = IntegerField()
    uloc                = IntegerField()
    dryness             = FloatField(null=True)
    num_files           = IntegerField() # Derived on load from number of files in relation below..
    # fmt:

    class Meta:
        """Define peewee meta data."""

        table_name = "scc"
        indexes = ((("scan", "name"), True),)


class SccFile(BaseModel):
    """Scc file-specific breakdown for a specific language."""

    # fmt: off
    scc                 = ForeignKeyField(Scc, backref='scc_file', on_delete='CASCADE')
    location            = CharField() # eg. src/qyx/__main__.py
    filename            = CharField() # eg. __main__.py
    directory           = CharField() # eg. src/qyx/
    extension           = CharField() # eg. py
    bytes               = IntegerField()
    lines               = IntegerField()
    code                = IntegerField()
    comment             = IntegerField()
    blank               = IntegerField()
    complexity          = IntegerField()
    weighted_complexity = IntegerField()
    binary              = BooleanField(default=False)
    minified            = BooleanField(default=False)
    generated           = BooleanField(default=False)
    endpoint            = IntegerField(default=0)
    uloc                = IntegerField()
    dryness             = FloatField(null=True)
    # fmt:

    class Meta:
        """Define peewee meta data."""

        table_name = "scc_file"
        indexes = ((("scc", "location"), True),)


################################################################################################
# RAW
################################################################################################
@query_cache
def query_scc_0(args: Namespace, scan: Scan, context: Vc = Vc.TOOL_HOME) -> Sns:
    query = Scc.select().where(Scc.scan == scan).dicts()
    rows = [Sns(**row_dict) for row_dict in query]

    # Calculate grand totals
    gt_ = defaultdict(int)
    for row in rows:
        for attr in ("num_files", "lines", "blank", "comment", "code", "uloc"):
            gt_[attr] += getattr(row, attr)
    sns_gt = Sns(**gt_)

    # Calculate "net" dryness across all languages
    sns_gt.dryness = (sns_gt.uloc / sns_gt.code) * 100.0
    return Sns(rows=rows, grand_totals=sns_gt)
