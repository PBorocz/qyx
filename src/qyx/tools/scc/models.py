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
    query = Scc.select().where(Scc.scan == scan)

    # Transpose so that each attr is a row, consisting of desired languages
    report_languages = args.config.get("tools.scc.settings.report_languages")
    transposed = {}
    for attr in ("num_files", "lines", "blank", "comment", "code", "uloc"):
        transposed[attr] = {}
        for row_dict in query.dicts():
            if row_dict["name"] in report_languages:
                transposed[attr][row_dict["name"]] = row_dict.get(attr)

    # Add calculated DRYness of each language we're reporting on.
    dryness = {}
    for lang in report_languages:
        dryness[lang] = round((transposed["uloc"][lang] / transposed["code"][lang]) * 100.0 + 0.5)

    # Convert to Sns
    rows = []
    for attr, languages in transposed.items():
        rows.append(Sns(attr=attr, languages=languages))

    # Calculate grand totals
    gt_ = defaultdict(int)
    for row in rows:
        gt_[row.attr] = sum(row.languages.values())
    sns_gt = Sns(**gt_)

    return Sns(
        rows=rows,
        dryness=dryness,
        grand_totals=sns_gt,
        report_languages=report_languages,
    )
