"""..."""

import logging
from argparse import Namespace
from collections import defaultdict
from types import SimpleNamespace as Sns

import peewee as pw

from qyx.constants import ViewContext as Vc
from qyx.tools._models_ import BaseModel, Scan
from qyx.utils.caching import query_cache


log = logging.getLogger(__name__)


class Scc(BaseModel):
    """Scc language summary."""

    # fmt: off
    id                  = pw.AutoField()
    scan                = pw.ForeignKeyField(Scan, on_delete="CASCADE")
    name                = pw.CharField()
    bytes               = pw.IntegerField()
    code_bytes          = pw.IntegerField()
    lines               = pw.IntegerField()
    code                = pw.IntegerField()
    comment             = pw.IntegerField()
    blank               = pw.IntegerField()
    complexity          = pw.IntegerField()
    count               = pw.IntegerField()
    weighted_complexity = pw.IntegerField()
    uloc                = pw.IntegerField()
    dryness             = pw.FloatField(null=True)
    num_files           = pw.IntegerField() # Derived on load from number of files in relation below..
    # fmt:

    class Meta:
        """Define peewee meta data."""

        table_name = "scc"
        indexes = ((("scan", "name"), True),)


class SccFile(BaseModel):
    """Scc file-specific breakdown for a specific language."""

    # fmt: off
    scc                 = pw.ForeignKeyField(Scc, backref='scc_file', on_delete='CASCADE')
    location            = pw.CharField() # eg. src/qyx/__main__.py
    filename            = pw.CharField() # eg. __main__.py
    directory           = pw.CharField() # eg. src/qyx/
    extension           = pw.CharField() # eg. py
    bytes               = pw.IntegerField()
    lines               = pw.IntegerField()
    code                = pw.IntegerField()
    comment             = pw.IntegerField()
    blank               = pw.IntegerField()
    complexity          = pw.IntegerField()
    weighted_complexity = pw.IntegerField()
    binary              = pw.BooleanField(default=False)
    minified            = pw.BooleanField(default=False)
    generated           = pw.BooleanField(default=False)
    endpoint            = pw.IntegerField(default=0)
    uloc                = pw.IntegerField()
    dryness             = pw.FloatField(null=True)
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
