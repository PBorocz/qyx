"""..."""

import logging
from argparse import Namespace
from collections import defaultdict
from types import SimpleNamespace as Sns

import peewee as pw
from peewee import fn

from qyx.constants import ViewContext as Vc
from qyx.tools._models_ import BaseModel, Project, Scan
from qyx.tools.common import get_scans_for_project_analysis
from qyx.utils.caching import query_cache
from qyx.utils.scoring import score_metric
from qyx.utils import rate_of_change_percentage


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
        i_dryness = round((transposed["uloc"][lang] / transposed["code"][lang]) * 100.0 + 0.5)
        dryness[lang] = score_metric(args, "tools.scc.dryness", i_dryness)

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


@query_cache
def query_scc_1(args: Namespace, scan: Scan, context: Vc = Vc.TOOL_HOME) -> Sns:
    query = (
        Scc.select(
            SccFile.directory,
            fn.SUM(SccFile.bytes),
            fn.SUM(SccFile.lines),
            fn.SUM(SccFile.code),
            fn.SUM(SccFile.comment),
            fn.SUM(SccFile.blank),
            fn.SUM(SccFile.complexity),
            fn.SUM(SccFile.uloc),
            fn.AVG(SccFile.weighted_complexity),
            fn.AVG(SccFile.dryness),
        )
        .join(SccFile)
        .where(Scc.scan == scan, SccFile.extension == "py")  # FIXME!
        .group_by(SccFile.directory)
        .order_by(SccFile.directory)
        .dicts()
    )
    return Sns(rows=[Sns(**row_dict) for row_dict in query])


@query_cache
def query_scc_2(args: Namespace, scan: Scan, context: Vc = Vc.TOOL_HOME) -> Sns:
    query = (
        Scc.select(
            SccFile.directory,
            SccFile.filename,
            SccFile.bytes,
            SccFile.lines,
            SccFile.code,
            SccFile.comment,
            SccFile.blank,
            SccFile.complexity,
            SccFile.uloc,
            SccFile.weighted_complexity,
            SccFile.dryness,
        )
        .join(SccFile)
        .where(Scc.scan == scan, SccFile.extension == "py")  # FIXME!
        .order_by(SccFile.directory, SccFile.filename)
        .dicts()
    )
    return Sns(rows=[Sns(**row_dict) for row_dict in query])


@query_cache
def query_scc_h(project: Project, last: int = None) -> Sns:
    scans = get_scans_for_project_analysis(project, "scc", last=last)
    query = (
        Scc.select(
            Scan.as_of.alias("timestamp"),
            Scan.git_commit_message.alias("message"),
            Scc.name,
            Scc.lines,
            Scc.code,
            Scc.comment,
            Scc.blank,
            Scc.complexity,
            Scc.uloc,
            Scc.dryness,
        )
        .join(Scan)
        .where(Scan.id.in_([scan.id for scan in scans]), Scc.name == "Python")  # FIXME!
        .order_by(Scan.as_of)
        .objects()
    )
    timestamps = [result.timestamp for result in query]
    messages = {result.timestamp: result.message for result in query}

    ################################################################################################
    # Transpose (to get timestamps *across* instead of down and calculate grand totals)
    ################################################################################################
    transposed = defaultdict(lambda: defaultdict(dict))
    grand_totals = defaultdict(int)
    attrs = ("lines", "code", "comment", "blank", "complexity", "uloc", "dryness")
    for row in query:
        for attr in attrs:
            transposed[attr][row.timestamp] = getattr(row, attr)

    # Calculate rate of change (primarily for CLI reporting)
    roc = dict()
    for attr in attrs:
        if len(timestamps) > 1:
            roc[attr] = rate_of_change_percentage(
                transposed[attr][timestamps[-2]],
                transposed[attr][timestamps[-1]],
            )
        else:
            roc[attr] = 0.00

    return Sns(
        rows=query,
        timestamps=timestamps,
        messages=messages,
        transposed=transposed,
        roc=roc,
    )
