"""..."""

import logging
from argparse import Namespace
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Literal

from peewee import fn, CharField, FloatField, IntegerField, ForeignKeyField

from mq.constants import ReportLevel
from mq.tools.base import BaseModel, BaseResultsModel, Project, Request, Scan
from mq.tools.common import get_scans_for_pta
from mq.utils import rate_of_change_percentage
from mq.utils.scoring import score_metric


log = logging.getLogger(__name__)


class RadonRaw(BaseResultsModel):
    """Radon "RAW" metric storage."""

    # NOTE: LOC = SLOC + Multi + Comments + Blanks
    # fmt: off
    loc             = IntegerField(help_text="Lines of code")
    sloc            = IntegerField(help_text="Source lines of code")
    comments        = IntegerField(help_text="Comment lines")
    multi           = IntegerField(help_text="Multi-line strings")
    blank           = IntegerField(help_text="Blank lines")
    lloc            = IntegerField(help_text="Logical lines of code")
    single_comments = IntegerField(help_text="Single-line comments")
    # fmt: on

    class Meta:
        """Define peewee meta data."""

        table_name = "radon_raw"
        indexes = ((("scan", "directory", "filename"), True),)

    @classmethod
    def attrs(cls) -> tuple[str]:
        """Return the "core" list of attributes (the other 2 are FYI)."""
        return ("loc", "sloc", "comments", "multi", "blank")


class RadonMi(BaseResultsModel):
    """Radon "MI" metric storage."""

    # fmt: off
    mi   = FloatField(help_text="Maintainability index")
    rank = CharField(help_text="Grade, ie. A, B, C, etc.")
    # fmt: on

    class Meta:
        """Define peewee meta data."""

        table_name = "radon_mi"
        indexes = ((("scan", "directory", "filename"), True),)


class RadonCc(BaseResultsModel):
    """Radon "CC" metric storage."""

    # fmt: off
    entity_type   = CharField(help_text="Function, Method or Class)")
    entity_name   = CharField(help_text="main, <class>.method, etc.")
    line_start    = IntegerField()
    line_end      = IntegerField()
    column_offset = IntegerField()
    rank          = CharField(help_text="Complexity grade, ie. A, B, C...")
    complexity    = IntegerField(help_text="Raw complexity score")
    # fmt: on

    def get_rank(self, complexity: float) -> str:
        """Return the grade score (aka "rank") for the given complexity measure."""
        if complexity < 5.0:
            return "A"  # low - simple block
        elif 5.0 <= complexity < 10.0:
            return "B"  # low - well structured and stable block
        elif 10.0 <= complexity < 20.0:
            return "C"  # moderate - slightly complex block
        elif 20.0 <= complexity < 30.0:
            return ReportLevel.DERIVED  # more than moderate - more complex block
        elif 30.0 <= complexity < 40.0:
            return "E"  # high - complex block, alarming
        else:
            return "F"  # very high - error-prone, unstable block

    class Meta:
        """Define peewee meta data."""

        table_name = "radon_cc"
        indexes = ((("scan", "directory", "filename", "entity_type", "entity_name", "line_start", "line_end"), True),)


class RadonHal(BaseResultsModel):
    """Radon "HAL" metric storage."""

    # fmt: off
    h1		       = IntegerField () # See below for descriptions...
    h2		       = IntegerField ()
    N1		       = IntegerField ()
    N2		       = IntegerField ()
    program_vocabulary = IntegerField ()
    program_length     = IntegerField ()
    calculated_length  = FloatField   ()
    volume             = FloatField   ()
    difficulty         = FloatField   ()
    effort             = FloatField   ()
    time               = FloatField   ()
    bugs               = FloatField   ()
    # fmt:

    @classmethod
    def attrs(cls):
        """Return a list of the attributes/metrics for the model (display, calculation, attr, type)."""
        # fmt: off
        return (
            #              Display                      Calculation                  ShortName              Type
            ModelAttribute("Estimated Bugs For File"  , "(V / 3000)"               , "bugs"               , "float"),
            ModelAttribute("Total Time"               , "(E / 18 seconds)"         , "time"               , "float"),
            ModelAttribute("Total Effort"             , "(E = D * V)"              , "effort"             , "float"),
            ModelAttribute("Mean Difficulty"          , "(D = ((h1/2) * (N2/h2)))" , "difficulty"         , "float"),
            ModelAttribute("Volume"                   , "(V = N log2 h))"          , "volume"             , "float"),
            ModelAttribute("Calculated Length"        , ""                         , "calculated_length"  , "float"),
            ModelAttribute("Program Length"           , "(N = N1 + N2)"            , "program_length"     , "int"  ),
            ModelAttribute("Program Vocabulary"       , "(h = h1 + h2)"            , "program_vocabulary" , "int"  ),
            ModelAttribute("Total Operands in File"   , "(N2)"                     , "N2"                 , "int"  ),
            ModelAttribute("Total Operators in File"  , "(N1)"                     , "N1"                 , "int"  ),
            ModelAttribute("Total Distinct Operands"  , "(h2)"                     , "h2"                 , "int"  ),
            ModelAttribute("Total Distinct Operators" , "(h1)"                     , "h1"                 , "int"  ),
        )
        # fmt: on

    class Meta:
        """Define peewee meta data."""

        table_name = "radon_hal"
        indexes = ((("scan", "directory", "filename"), True),)


class RadonHalFunction(BaseModel):
    """Radon "HAL" Function metric storage."""

    # fmt: off
    scan              = ForeignKeyField(Scan, backref="radon_hal_functions_scan", on_delete="CASCADE")
    radon_hal         = ForeignKeyField(RadonHal, backref="radon_hal_functions", on_delete="CASCADE")

    name              = CharField(help_text="function name")
    h1		      = IntegerField(help_text="Total distinct operators")
    h2		      = IntegerField(help_text="Total distinct operands")
    N1		      = IntegerField(help_text="Total operators in file")
    N2		      = IntegerField(help_text="Total operands in file")
    program_vocabulary= IntegerField(help_text="Total vocabulary (h = h1 + h2)")
    program_length    = IntegerField(help_text="Total length (N = N1 + N2)")
    calculated_length = IntegerField(help_text="(see wikipedia page!)")
    volume            = FloatField(help_text="Total volume (V = N log2 h)")
    difficulty        = FloatField(help_text="Mean difficulty across functions (D = ((h1/2) * (N2/h2)))")
    effort            = FloatField(help_text="Total effort (E = D * V)")
    time              = FloatField(help_text="Total time (T = (E / 18) in seconds)")
    bugs              = FloatField(help_text="Estimated bugs for file (B = V / 3000)")
    # fmt:

    class Meta:
        """Define peewee meta data."""

        table_name = "radon_hal_function"
        indexes = ((("radon_hal", "name"), True),)


################################################################################################
# RAW
################################################################################################
def query_raw(
    args: Namespace,
    level: str = ReportLevel.SUMMARY,
    scan: Scan = None,
    project: Project = None,
    last: int = None,
) -> Any:
    match level.lower():
        case ReportLevel.SUMMARY:
            return _query_raw_0(args, scan)
        case ReportLevel.DIRECTORY:
            return _query_raw_1(args, scan)
        case ReportLevel.FILE:
            return _query_raw_2(args, scan)
        case ReportLevel.HISTORY:
            return _query_raw_h(args, project, last)
        case _:
            raise RuntimeError(f"Sorry, invalid query level encountered! {level}")


def _query_raw_0(args: Namespace, scan: Scan) -> Any:
    row = (
        RadonRaw.select(
            fn.SUM(RadonRaw.blank).alias("blank"),
            fn.SUM(RadonRaw.comments).alias("comments"),
            fn.SUM(RadonRaw.loc).alias("loc"),
            fn.SUM(RadonRaw.multi).alias("multi"),
            fn.SUM(RadonRaw.sloc).alias("sloc"),
        )
        .where(RadonRaw.scan == scan)
        .first()
    )

    # Convert to percentage of total:
    # fmt: off
    row.blank_p    = (row.blank    / row.loc) * 100.0
    row.comments_p = (row.comments / row.loc) * 100.0
    row.multi_p    = (row.multi    / row.loc) * 100.0
    row.sloc_p     = (row.sloc     / row.loc) * 100.0
    # fmt: on

    return row


def _query_raw_1(args: Namespace, scan: Scan) -> Any:
    rows = (
        RadonRaw.select(
            RadonRaw.directory,
            fn.SUM(RadonRaw.blank).alias("blank"),
            fn.SUM(RadonRaw.comments).alias("comments"),
            fn.SUM(RadonRaw.loc).alias("loc"),
            fn.SUM(RadonRaw.multi).alias("multi"),
            fn.SUM(RadonRaw.sloc).alias("sloc"),
        )
        .where(RadonRaw.scan == scan)
        .group_by(RadonRaw.directory)
        .order_by(RadonRaw.directory)
    )

    # Calculate totals
    totals = defaultdict(int)
    for row in rows:
        for attr_name in RadonRaw.attrs():
            totals[attr_name] += getattr(row, attr_name)
    return rows, totals


def _query_raw_2(args: Namespace, scan: Scan) -> Any:
    return RadonRaw.select().where(RadonRaw.scan == scan).order_by(RadonRaw.directory, RadonRaw.filename)


def _query_raw_h(args: Namespace, project: Project, last: int = None) -> Any:
    scans = get_scans_for_pta(project, tool="radon", analysis="raw", last=last)
    query = (
        RadonRaw.select(
            Scan.as_of.alias("timestamp"),
            Scan.git_commit_message.alias("message"),
            fn.SUM(RadonRaw.blank).alias("blank"),
            fn.SUM(RadonRaw.comments).alias("comments"),
            fn.SUM(RadonRaw.loc).alias("loc"),
            fn.SUM(RadonRaw.multi).alias("multi"),
            fn.SUM(RadonRaw.sloc).alias("sloc"),
        )
        .join(Scan)
        .where(Scan.id.in_(scans))
        .group_by(Scan.as_of)
        .order_by(Scan.as_of)
        .objects()
    )
    timestamps = [result.timestamp for result in query]
    messages = {result.timestamp: result.message for result in query}

    ################################################################################################
    # Transpose (to get timestamps *across* instead of down and calculate grand totals)
    ################################################################################################
    timestamps = [result.timestamp for result in query]
    transposed = defaultdict(lambda: defaultdict(dict))
    for result in query:
        total = 0
        for attr_name in RadonRaw.attrs():
            lines = int(getattr(result, attr_name))
            transposed[attr_name][result.timestamp] = lines
            total += lines  # Calculate grand totals for each timestamp as we go

    # Calculate rate of change of last 2 entries..
    rocs = dict()
    for attr_name in RadonRaw.attrs():
        if len(timestamps) > 1:
            rocs[attr_name] = rate_of_change_percentage(
                transposed[attr_name][timestamps[-2]],
                transposed[attr_name][timestamps[-1]],
            )
        else:
            rocs[attr_name] = 0.0

    if len(timestamps) > 1:
        roc_gt = rate_of_change_percentage(
            transposed["loc"][timestamps[-2]],
            transposed["loc"][timestamps[-1]],
        )
    else:
        roc_gt = 0.0

    return timestamps, messages, transposed, rocs, roc_gt


################################################################################################
# HAL
################################################################################################
def query_hal(
    args: Namespace,
    level: str = ReportLevel.SUMMARY,
    scan: Scan = None,
    project: Project = None,
    last: int = None,
) -> Any:
    match level.lower():
        case ReportLevel.SUMMARY:
            return _query_hal_0(args, scan)
        case ReportLevel.DIRECTORY:
            return _query_hal_1(args, scan)
        case ReportLevel.FILE:
            return _query_hal_2(args, scan)
        case ReportLevel.DETAIL:
            return _query_hal_3(args, scan)
        case ReportLevel.DERIVED:
            return _query_hal_d(args, project, scan)
        case ReportLevel.HISTORY:
            return _query_hal_h(args, project, last)
        case _:
            raise RuntimeError(f"Sorry, invalid query level requested {level=}")


def _query_hal_0(args: Namespace, scan: Scan) -> Any:
    return (
        RadonHal.select(
            fn.AVG(RadonHal.h1).alias("h1"),
            fn.AVG(RadonHal.h2).alias("h2"),
            fn.AVG(RadonHal.N1).alias("N1"),
            fn.AVG(RadonHal.N2).alias("N2"),
            fn.AVG(RadonHal.program_vocabulary).alias("program_vocabulary"),
            fn.AVG(RadonHal.program_length).alias("program_length"),
            fn.AVG(RadonHal.calculated_length).alias("calculated_length"),
            fn.AVG(RadonHal.volume).alias("volume"),
            fn.AVG(RadonHal.difficulty).alias("difficulty"),
            fn.AVG(RadonHal.effort).alias("effort"),
            fn.AVG(RadonHal.time).alias("time"),
            fn.AVG(RadonHal.bugs).alias("bugs"),
        )
        .where(
            RadonHal.scan == scan,
        )
        .get()
    )


def _query_hal_1(args: Namespace, scan: Scan) -> Any:
    rows = (
        RadonHal.select(
            RadonHal.directory,
            fn.AVG(RadonHal.h1).alias("h1"),
            fn.AVG(RadonHal.h2).alias("h2"),
            fn.AVG(RadonHal.N1).alias("N1"),
            fn.AVG(RadonHal.N2).alias("N2"),
            fn.AVG(RadonHal.program_vocabulary).alias("program_vocabulary"),
            fn.AVG(RadonHal.program_length).alias("program_length"),
            fn.AVG(RadonHal.calculated_length).alias("calculated_length"),
            fn.AVG(RadonHal.volume).alias("volume"),
            fn.AVG(RadonHal.difficulty).alias("difficulty"),
            fn.AVG(RadonHal.effort).alias("effort"),
            fn.AVG(RadonHal.time).alias("time"),
            fn.AVG(RadonHal.bugs).alias("bugs"),
        )
        .group_by(RadonHal.directory)
        .where(RadonHal.scan == scan)
        .order_by(RadonHal.directory)
    )
    # Calculate mean of the means
    mean_means = {}
    for attr in RadonHal.attrs():
        values = [getattr(row, attr.name) for row in rows]
        mean_means[attr.name] = sum(values) / len(values) if values else None

    return rows, mean_means


def _query_hal_2(args: Namespace, scan: Scan) -> Any:
    rows = RadonHal.select().where(RadonHal.scan == scan).order_by(RadonHal.directory, RadonHal.filename)

    # Calculate means
    means = {}
    for attr in RadonHal.attrs():
        values = [getattr(row, attr.name) for row in rows]
        means[attr.name] = sum(values) / len(values) if values else None
    return rows, means


def _query_hal_3(args: Namespace, scan: Scan) -> Any:
    rows = (
        RadonHalFunction.select(
            RadonHal.directory,
            RadonHal.filename,
            RadonHalFunction.name,
            RadonHalFunction.h1,
            RadonHalFunction.h2,
            RadonHalFunction.N1,
            RadonHalFunction.N2,
            RadonHalFunction.program_vocabulary,
            RadonHalFunction.program_length,
            RadonHalFunction.calculated_length,
            RadonHalFunction.volume,
            RadonHalFunction.difficulty,
            RadonHalFunction.effort,
            RadonHalFunction.time,
            RadonHalFunction.bugs,
        )
        .join(RadonHal)
        .where(RadonHal.scan == scan)
        .order_by(RadonHal.directory, RadonHal.filename, RadonHalFunction.name)
        .objects()
    )
    # Calculate mean metric values
    means = {}
    for attr in RadonHal.attrs():
        values = [getattr(row, attr.name) for row in rows]
        means[attr.name] = sum(values) / len(values) if values else None

    return rows, means


def _query_hal_h(args: Namespace, project: Project = None, last: int = 5) -> Any:
    scans = get_scans_for_pta(project, tool="radon", analysis="hal", last=last)
    query = (
        RadonHal.select(
            Scan.as_of.alias("timestamp"),
            Scan.git_commit_message.alias("message"),
            fn.AVG(RadonHal.h1).alias("h1"),
            fn.AVG(RadonHal.h2).alias("h2"),
            fn.AVG(RadonHal.N1).alias("N1"),
            fn.AVG(RadonHal.N2).alias("N2"),
            fn.AVG(RadonHal.program_vocabulary).alias("program_vocabulary"),
            fn.AVG(RadonHal.program_length).alias("program_length"),
            fn.AVG(RadonHal.calculated_length).alias("calculated_length"),
            fn.AVG(RadonHal.volume).alias("volume"),
            fn.AVG(RadonHal.difficulty).alias("difficulty"),
            fn.AVG(RadonHal.effort).alias("effort"),
            fn.AVG(RadonHal.time).alias("time"),
            fn.AVG(RadonHal.bugs).alias("bugs"),
        )
        .join(Scan)
        .where(Scan.id.in_(scans))
        .group_by(Scan.as_of)
        .order_by(Scan.as_of)
        .objects()
    )
    timestamps = [result.timestamp for result in query]
    messages = {result.timestamp: result.message for result in query}

    ################################################################################################
    # Transpose (to get timestamps *across* instead of down and calculate grand totals)
    ################################################################################################
    transposed = defaultdict(lambda: defaultdict(dict))
    for result in query:
        total = 0
        for attr in RadonHal.attrs():
            value = getattr(result, attr.name)
            transposed[attr.name][result.timestamp] = value
            total += value  # Calculate grand totals for each timestamp as we go

    # Calculate rate of change of last 2 entries..
    rocs = dict()
    for attr in RadonHal.attrs():
        if len(timestamps) > 1:
            rocs[attr.name] = rate_of_change_percentage(
                transposed[attr.name][timestamps[-2]],
                transposed[attr.name][timestamps[-1]],
            )
        else:
            rocs[attr] = 0.00

    return timestamps, messages, transposed, rocs


def _query_hal_d(args: Namespace, project: Project, scan: Scan):
    """Calculate derived radon-hal metric(s)."""
    raw = _query_raw_0(args, scan=Scan.get_most_recent(project, "radon", "raw"))
    row = _query_hal_0(args, scan)

    ################################################################################
    # Calculate all HAL metrics
    ################################################################################
    # Score Halstead effort per 1000 source lines of code.
    metric_value = (row.bugs / raw.sloc) * 1000
    row.bugs_d = score_metric(args, "tools.radon.hal.bugs", metric_value)

    # Score Halstead effort per source line of code.
    metric_value = row.effort / raw.sloc
    row.effort_d = score_metric(args, "tools.radon.hal.effort", metric_value)

    # Score Halstead difficulty metric.
    row.difficulty_d = score_metric(args, "tools.radon.hal.difficulty", row.difficulty)

    # Composite (after the above have been calculated!)
    difficulty_score = max(0, 100 - (row.difficulty_d.score / 40) * 100)
    bugs_score = max(0, 100 - (row.bugs_d.score / 1.0) * 100)
    effort_score = max(0, 100 - (row.effort_d.score / 1000) * 100)
    metric_value = bugs_score * 0.5 + difficulty_score * 0.3 + effort_score * 0.2
    row.composite_d = score_metric(args, "tools.radon.hal.composite", metric_value)

    return row


################################################################################################
# MI
################################################################################################
def query_mi(
    args: Namespace,
    level: str = ReportLevel.SUMMARY,
    scan: Scan = None,
    project: Project = None,
    last: int = None,
) -> Any:
    match level.lower():
        case ReportLevel.SUMMARY:
            return _query_mi_0(args, scan)
        case ReportLevel.DIRECTORY:
            return _query_mi_1(args, scan)
        case ReportLevel.FILE:
            return _query_mi_2(args, scan)
        case ReportLevel.DERIVED:
            return _query_mi_d(args, scan)
        case ReportLevel.HISTORY:
            return _query_mi_h(args, project, last)
        case _:
            raise RuntimeError(f"Sorry, invalid query level encountered! {level}")


def _query_mi_0(args: Namespace, mi_scan: Scan):
    """Calculate LOC-weighted Maintainability Index (using latest loc/raw RAW scan)."""
    raw_scan = Scan.get_most_recent(mi_scan.request.project, "radon", "raw")
    query = (
        RadonMi.select(
            fn.SUM(RadonRaw.loc * RadonMi.mi).alias("weighted_sum"),
            fn.SUM(RadonRaw.loc).alias("total_loc"),
        )
        .join(
            RadonRaw,
            on=(
                (RadonRaw.scan_id == raw_scan.id)
                & (RadonMi.directory == RadonRaw.directory)
                & (RadonMi.filename == RadonRaw.filename)
            ),
        )
        .where(RadonMi.scan_id == mi_scan.id)
    )
    result = query.dicts().get()
    if result["total_loc"]:
        return result["weighted_sum"] / result["total_loc"]
    return None


def _query_mi_1(args: Namespace, mi_scan: Scan) -> Any:
    raw_scan = Scan.get_most_recent(mi_scan.request.project, "radon", "raw")
    query = (
        RadonMi.select(
            RadonMi.directory,
            fn.SUM(RadonMi.mi * RadonRaw.loc).alias("weighted_sum"),
            fn.SUM(RadonRaw.loc).alias("total_loc"),
        )
        .join(
            RadonRaw,
            on=(
                (RadonRaw.scan_id == raw_scan.id)
                & (RadonMi.directory == RadonRaw.directory)
                & (RadonMi.filename == RadonRaw.filename)
            ),
        )
        .where(RadonMi.scan_id == mi_scan.id)
        .group_by(RadonMi.directory)
    )
    mi_by_directory = {
        row["directory"]: row["weighted_sum"] / row["total_loc"] for row in query.dicts() if row["total_loc"]
    }
    mi_ = _query_mi_0(args, mi_scan)
    return mi_, mi_by_directory


def _query_mi_2(args: Namespace, scan: Scan) -> tuple:
    rows = RadonMi.select().where(RadonMi.scan == scan).order_by(RadonMi.mi.asc(), RadonMi.directory, RadonMi.filename)
    mi_ = _query_mi_0(args, scan)
    return mi_, rows


def _query_mi_h(args: Namespace, project, last: int = 5) -> Any:
    assert project

    mi_scans = get_scans_for_pta(project, tool="radon", analysis="mi", last=last)
    mi_scan_ids = [scan.id for scan in mi_scans]

    # Alias for the RAW scan to make the query clearer
    RawScan = Scan.alias()

    query = (
        RadonMi.select(
            Scan.as_of.alias("timestamp"),
            Scan.git_commit_message.alias("message"),
            (fn.SUM(RadonMi.mi * RadonRaw.loc) / fn.SUM(RadonRaw.loc)).alias("mi_weighted"),
        )
        .join(
            Scan,
            on=(RadonMi.scan == Scan.id),
        )
        .switch(RadonMi)
        .join(
            RadonRaw,
            on=((RadonMi.directory == RadonRaw.directory) & (RadonMi.filename == RadonRaw.filename)),
        )
        .join(
            RawScan,
            on=(
                (RadonRaw.scan == RawScan.id)
                & (RawScan.request == Scan.request)
                & (RawScan.tool == "radon")
                & (RawScan.analysis == "raw")
            ),
        )
        .where(RadonMi.scan.in_(mi_scan_ids))
        .group_by(Scan.as_of)
        .order_by(Scan.as_of.desc())
    )
    rows = {row["timestamp"]: row["mi_weighted"] for row in query.dicts()}
    messages = {row["timestamp"]: row["message"] for row in query.dicts()}

    # Calculate rate of change of last 2 entries..
    timestamps = list(rows.keys())
    roc = 0.00
    if len(timestamps) > 1:
        ts_penultimate, ts_last = sorted(timestamps)[-2:]
        roc = rate_of_change_percentage(rows[ts_penultimate], rows[ts_last])

    return messages, rows, roc


def _query_mi_d(args: Namespace, scan: Scan):
    """Calculate derived radon-mi metric(s)."""
    mi_ = _query_mi_0(args, scan)
    return score_metric(args, "tools.radon.mi.mean", mi_)


################################################################################################
# CC
################################################################################################
def query_cc(
    args: Namespace,
    level: str = ReportLevel.SUMMARY,
    scan: Scan = None,
    project: Project = None,
    last: int = None,
) -> Any:
    match level.lower():
        case ReportLevel.SUMMARY:
            return _query_cc_0(args, scan)
        case ReportLevel.DIRECTORY:
            return _query_cc_1(args, scan)
        case ReportLevel.FILE:
            return _query_cc_2(args, scan)
        case ReportLevel.DETAIL:
            return _query_cc_3(args, scan)
        case ReportLevel.DERIVED:
            return _query_cc_d(args, scan)
        case ReportLevel.HISTORY:
            return _query_cc_h(args, project, last)
        case _:
            raise RuntimeError(f"Sorry, invalid query level encountered! {level}")


def _query_cc_0(args: Namespace, scan: Scan) -> Any:
    return (
        RadonCc.select(
            RadonCc.entity_type.alias("entity_type"),
            fn.AVG(RadonCc.complexity).alias("mean_complexity"),
        )
        .where(RadonCc.scan == scan)
        .group_by(RadonCc.entity_type)
        .order_by(fn.COUNT(RadonCc.id).desc())
    )


def _query_cc_1(args: Namespace, scan: Scan) -> Any:
    return (
        RadonCc.select(
            RadonCc.directory,
            RadonCc.entity_type,
            fn.AVG(RadonCc.complexity).alias("mean_complexity"),
        )
        .where(RadonCc.scan == scan)
        .group_by(RadonCc.directory, RadonCc.entity_type)
        .order_by(RadonCc.directory, RadonCc.entity_type)
    )


def _query_cc_2(args: Namespace, scan: Scan) -> Any:
    return (
        RadonCc.select(
            RadonCc.directory,
            RadonCc.filename,
            RadonCc.entity_type,
            fn.AVG(RadonCc.complexity).alias("mean_complexity"),
        )
        .where(RadonCc.scan == scan)
        .group_by(RadonCc.directory, RadonCc.filename, RadonCc.entity_type)
        .order_by(RadonCc.directory, RadonCc.filename, RadonCc.entity_type)
    )


def _query_cc_3(args: Namespace, scan: Scan) -> Any:
    return (
        RadonCc.select().where(RadonCc.scan == scan).order_by(RadonCc.directory, RadonCc.filename, RadonCc.entity_name)
    )


def _query_cc_h(args: Namespace, project: Project, last: int = None) -> Any:
    scans = get_scans_for_pta(project, tool="radon", analysis="cc", last=last)
    query = (
        RadonCc.select(
            Scan.as_of.alias("timestamp"),
            Scan.git_commit_message.alias("message"),
            RadonCc.entity_type,
            fn.AVG(RadonCc.complexity).alias("complexity"),
        )
        .join(Scan)
        .where(Scan.id.in_(scans))
        .group_by(Scan.as_of, RadonCc.entity_type)
        .order_by(Scan.as_of)
        .objects()
    )
    timestamps = list({result.timestamp for result in query})
    messages = {result.timestamp: result.message for result in query}

    ################################################################################################
    # Transpose (to get timestamps *across* instead of down and calculate grand totals)
    ################################################################################################
    transposed = defaultdict(lambda: defaultdict(dict))
    for result in query:
        transposed[result.entity_type][result.timestamp] = result.complexity

    # Calculate rate of change of last 2 entries for each entity type
    rocs = dict()
    if len(timestamps) > 1:
        for entity_type, values_by_timestamp in transposed.items():
            rocs[entity_type] = rate_of_change_percentage(
                values_by_timestamp[timestamps[-2]],
                values_by_timestamp[timestamps[-1]],
            )

    return timestamps, messages, transposed, rocs


def _query_cc_d(args: Namespace, scan: Scan):
    """Calculate derived radon-cc metric(s)."""
    # Standards reference:
    # - McCabe (1976)*: CC > 10 indicates high risk
    # - NIST          : CC > 15 is concerning, > 20 is dangerous
    from mq.tools.radon import RadonCcEntityType  # Circular import??

    results = _query_cc_0(args, scan)
    for result in results:
        threshold_type = (
            "tools.radon.cc.classes"
            if result.entity_type.upper() == RadonCcEntityType.CLASS.value
            else "tools.radon.cc.callables"  # ie. (F)unctions and (M)ethods
        )
        result.cc_d = score_metric(args, threshold_type, result.mean_complexity)

    return results


################################################################################################
# Supporting...
################################################################################################
@dataclass(frozen=True)
class ModelAttribute:
    """Represents a model attribute/metric with its metadata."""

    display: str
    calculation: str
    name: str
    type: Literal["float", "int", "str"]
