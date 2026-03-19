"""..."""

import logging
from argparse import Namespace
from collections import defaultdict
from types import SimpleNamespace as Sns

import peewee as pw
from peewee import fn

from qyx.constants import ALL_ITEMS
from qyx.constants import ViewContext as Vc
from qyx.tools._models_ import BaseModel, ModelAttribute, Project, Scan
from qyx.tools.common import get_scans_for_project_dimension
from qyx.utils import rate_of_change_percentage


log = logging.getLogger(__name__)


class Scc(BaseModel):
    """Scc language summary."""

    # fmt: off
    id                  = pw.AutoField()
    scan                = pw.ForeignKeyField(Scan, on_delete="CASCADE")
    language            = pw.CharField() # eg. python, html, markdown, license, css etc.
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

    @classmethod
    def attrs(cls):
        """Return the SCC attributes to report on *in order*!"""
        # fmt: off
        return (
            ModelAttribute("Num Files"    , "", "num_files"  , "int"),
            ModelAttribute("Lines of Code", "", "lines"      , "int"),
            # ModelAttribute("Code"        , "", "code"       , "int"),
            ModelAttribute("Unique Code"  , "", "uloc"       , "int"),
            ModelAttribute("Comments"     , "", "comment"    , "int"),
            ModelAttribute("Blanks"       , "", "blank"      , "int"),
            ModelAttribute("Complexity"   , "", "complexity" , "int"),
            ModelAttribute("Dryness"      , "", "dryness"    , "int"),
        )
        # fmt: off

    class Meta:
        """Define peewee meta data."""

        table_name = "tool_scc"
        indexes = ((("scan", "language"), True),)


class SccFile(BaseModel):
    """Scc file-specific breakdown for a specific language."""

    # fmt: off
    scc                 = pw.ForeignKeyField(Scc, backref='scc_file', on_delete='CASCADE')
    location            = pw.CharField() # eg. src/qyx/__main__.py
    filename            = pw.CharField() # eg. __main__.py
    directory           = pw.CharField() # eg. src/qyx/
    language            = pw.CharField() # eg. python, html, css, etc.
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

        table_name = "tool_scc_file"
        indexes = ((("scc", "location"), True),)


def query_scc_0(args: Namespace, scan: Scan, dimension: str, context: Vc = Vc.TOOL_HOME) -> Sns:
    query = Scc.select().where(Scc.scan == scan).dicts()  # Default is essentially wildcard!
    if not dimension:
        types = args.config.get("tools.scc.settings.dashboard_report_types")
        query = query.where(Scc.language.in_(types))
    elif dimension != ALL_ITEMS:
        query = query.where(fn.LOWER(Scc.language) == fn.LOWER(dimension))

    if not len(query):  # Make sure we got rows back
        return Sns()

    # Instead of each row being a file type, collapse so that each row has information on all types.
    d_rows = {}
    types_encountered = set()
    for attr in [attr for attr in query[0].keys() if attr not in ("id", "language")]:
        d_rows[attr] = {}
        for row_dict in query:
            d_rows[attr][row_dict["language"]] = int(row_dict.get(attr))
            types_encountered.add(row_dict["language"])

    # Return list of file types encountered in *sorted* order by total number of lines (thanks Claude!)
    values: list[int] = [d_rows["lines"][lang] for lang in types_encountered]
    types: list[str] = [lang for lang, _ in sorted(zip(types_encountered, values), key=lambda x: x[1], reverse=True)]

    # Calculate grand totals
    gt_ = defaultdict(int)
    for attr, types in d_rows.items():
        gt_[attr] = sum(types.values())
    sns_gt = Sns(**gt_)

    return Sns(types=types, rows=d_rows, grand_totals=sns_gt, attrs=Scc.attrs())


def query_scc_1(args: Namespace, scan: Scan, dimension: str, context: Vc = Vc.TOOL_HOME) -> Sns:
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
        .where(Scc.scan == scan, SccFile.language == dimension)
        .group_by(SccFile.directory)
        .order_by(SccFile.directory)
        .dicts()
    )
    return Sns(rows=[Sns(**row_dict) for row_dict in query])


def query_scc_2(args: Namespace, scan: Scan, dimension: str, context: Vc = Vc.TOOL_HOME) -> Sns:
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
        .where(Scc.scan == scan, SccFile.language == dimension)
        .order_by(SccFile.directory, SccFile.filename)
        .dicts()
    )
    return Sns(rows=[Sns(**row_dict) for row_dict in query])


def query_scc_h(project: Project, dimension: str, last: int = None) -> Sns:
    scans = get_scans_for_project_dimension(project, "scc", last=last)

    query = (
        Scc.select(
            Scan.as_of.alias("timestamp"),
            Scan.git_commit_message.alias("message"),
            Scc.language,
            Scc.lines,
            Scc.code,
            Scc.comment,
            Scc.blank,
            Scc.complexity,
            Scc.uloc,
            Scc.dryness,
        )
        .join(Scan)
        .where(
            Scan.id.in_([scan.id for scan in scans]),
            fn.LOWER(Scc.language) == fn.LOWER(dimension),
        )
        .order_by(Scan.as_of)
        .objects()
    )
    timestamps = [result.timestamp for result in query]
    messages_by_timestamp = {result.timestamp: result.message for result in query}

    ################################################################################################
    # Transpose (to get timestamps *across* instead of down and calculate grand totals)
    ################################################################################################
    transposed = defaultdict(lambda: defaultdict(dict))
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
        messages=messages_by_timestamp,
        transposed=transposed,
        roc=roc,
    )
