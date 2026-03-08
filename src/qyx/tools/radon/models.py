"""..."""

import logging
from argparse import Namespace
from collections import defaultdict
from dataclasses import dataclass
from types import SimpleNamespace as Sns
from typing import Literal

from peewee import fn, CharField, FloatField, IntegerField, ForeignKeyField

from qyx.constants import ViewContext as Vc
from qyx.tools.base import BaseModel, BaseResultsModel, Project, Request, Scan
from qyx.tools.common import get_scans_for_project_analysis
from qyx.utils import rate_of_change_percentage
from qyx.utils.caching import query_cache
from qyx.utils.scoring import score_metric


log = logging.getLogger(__name__)


class RadonRaw(BaseResultsModel):
    """Radon "RAW" metric storage."""

    # NOTE: LOC = Blanks + COmments + Multi + SingleComments + SLOC
    # fmt: off
    loc             = IntegerField(help_text="Lines of code")
    blank           = IntegerField(help_text="Blank lines")
    comments        = IntegerField(help_text="Comment lines")
    lloc            = IntegerField(help_text="Logical lines of code")
    multi           = IntegerField(help_text="Multi-line strings")
    single_comments = IntegerField(help_text="Single-line comments")
    sloc            = IntegerField(help_text="Source lines of code")
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

    @classmethod
    def entity_type_display(cls, entity_type: str) -> str:
        """Return the grade score (aka "rank") for the given complexity measure."""
        plurals = dict(C="Classes", F="Functions", M="Methods")
        return plurals.get(entity_type.upper(), None)

    @classmethod
    def get_threshold_type(cls, entity_type: str) -> str:
        """Return the appropriate threshold entry from the configuration file for the entity type."""
        return (
            "tools.radon.cc.classes"
            if entity_type.upper() == "C"  # HARD-CODE!
            else "tools.radon.cc.callables"
        )

    class Meta:
        """Define peewee meta data."""

        table_name = "radon_cc"
        indexes = (
            # Uniqueness criteria
            (("scan", "directory", "filename", "entity_type", "entity_name", "line_start", "line_end"), True),
            # Optimize for joining + grouping by entity_type
            (("scan", "entity_type"), False),
        )


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
@query_cache
def query_raw_0(args: Namespace, scan: Scan, context: Vc = Vc.TOOL_HOME) -> Sns:
    query = (
        RadonRaw.select(
            fn.SUM(RadonRaw.blank).alias("blank"),
            fn.SUM(RadonRaw.comments).alias("comments"),
            fn.SUM(RadonRaw.multi).alias("multi"),
            fn.SUM(RadonRaw.sloc).alias("sloc"),
            fn.SUM(RadonRaw.loc).alias("loc"),
        )
        .where(RadonRaw.scan == scan)
        .dicts()
        .first()
    )
    result: Sns = Sns(**query)

    # Convert to percentage of total:
    # fmt: off
    result.blank_p    = (result.blank    / result.loc) * 100.0
    result.comments_p = (result.comments / result.loc) * 100.0
    result.multi_p    = (result.multi    / result.loc) * 100.0
    result.sloc_p     = (result.sloc     / result.loc) * 100.0
    result.loc_p      = result.blank_p + result.comments_p + result.multi_p + result.sloc_p
    # fmt: on

    return result


@query_cache
def query_raw_1(scan: Scan) -> Sns:
    query = (
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
        .dicts()
    )
    rows = [Sns(**row_dict) for row_dict in query]

    # Calculate totals
    totals = defaultdict(int)
    for row in rows:
        for attr_name in RadonRaw.attrs():
            totals[attr_name] += getattr(row, attr_name)
    return Sns(rows=rows, totals=totals)


@query_cache
def query_raw_2(scan: Scan) -> Sns:
    query = (
        RadonRaw.select()
        .where(RadonRaw.scan == scan)
        .order_by(
            RadonRaw.directory,
            RadonRaw.filename,
        )
        .dicts()
    )
    rows = [Sns(**row_dict) for row_dict in query]

    # Calculate totals
    totals = defaultdict(int)
    for row in rows:
        for attr_name in RadonRaw.attrs():
            totals[attr_name] += getattr(row, attr_name)
    return Sns(rows=rows, totals=totals)


@query_cache
def query_raw_h(project: Project, last: int = None) -> Sns:
    scans = get_scans_for_project_analysis(project, "raw", last=last)
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
        .where(Scan.id.in_([scan.id for scan in scans]))
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

    return Sns(
        timestamps=timestamps,
        messages=messages,
        transposed=transposed,
        rocs=rocs,
        roc_gt=roc_gt,
    )


################################################################################################
# HAL
################################################################################################
@query_cache
def query_hal_0(args: Namespace, scan: Scan, context: Vc = Vc.TOOL_HOME) -> Sns:
    query = (
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
        .dicts()
        .get()
    )
    result: Sns = Sns(**query)
    if not result:
        return None

    ################################################################################
    # Calculate "derived" metrics based on the raws ones above.
    ################################################################################
    # Get SLOC values...
    raw = query_raw_0(args, scan=Scan.get_most_recent(scan.request.project, "radon", "raw"))

    # Score Halstead effort per 1000 source lines of code.
    metric_value = (result.bugs / raw.sloc) * 1000
    result.bugs_d = score_metric(args, "tools.radon.hal.bugs", metric_value)

    # Score Halstead effort per source line of code.
    metric_value = result.effort / raw.sloc
    result.effort_d = score_metric(args, "tools.radon.hal.effort", metric_value)

    # Score Halstead difficulty metric.
    result.difficulty_d = score_metric(args, "tools.radon.hal.difficulty", result.difficulty)

    # Composite (after the above have been calculated!)
    difficulty_score = max(0, 100 - (result.difficulty_d.score / 40) * 100)
    bugs_score = max(0, 100 - (result.bugs_d.score / 1.0) * 100)
    effort_score = max(0, 100 - (result.effort_d.score / 1000) * 100)
    metric_value = bugs_score * 0.5 + difficulty_score * 0.3 + effort_score * 0.2
    result.composite_d = score_metric(args, "tools.radon.hal.composite", metric_value)

    return result


@query_cache
def query_hal_1(scan: Scan) -> Sns:
    query = (
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
        .dicts()
    )
    rows = [Sns(**row_dict) for row_dict in query]

    # Calculate mean of the means
    mean_means = {}
    for attr in RadonHal.attrs():
        values = [getattr(row, attr.name) for row in rows]
        mean_means[attr.name] = sum(values) / len(values) if values else None

    return Sns(rows=rows, mean_means=mean_means)


@query_cache
def query_hal_2(scan: Scan) -> Sns:
    query = (
        RadonHal.select()
        .where(RadonHal.scan == scan)
        .order_by(
            RadonHal.directory,
            RadonHal.filename,
        )
        .dicts()
    )
    rows = [Sns(**row_dict) for row_dict in query]

    # Calculate means
    means = {}
    for attr in RadonHal.attrs():
        values = [getattr(row, attr.name) for row in rows]
        means[attr.name] = sum(values) / len(values) if values else None
    return Sns(rows=rows, means=means)


@query_cache
def query_hal_3(scan: Scan) -> Sns:
    query = (
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
        .dicts()
    )
    rows = [Sns(**row_dict) for row_dict in query]

    # Calculate mean metric values
    means = {}
    for attr in RadonHal.attrs():
        values = [getattr(row, attr.name) for row in rows]
        means[attr.name] = sum(values) / len(values) if values else None

    return Sns(rows=rows, means=means)


@query_cache
def query_hal_h(project: Project = None, last: int = None) -> Sns:
    scans = get_scans_for_project_analysis(project, "hal", last=last)
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
        .where(Scan.id.in_([scan.id for scan in scans]))
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

    return Sns(timestamps=timestamps, messages=messages, transposed=transposed, rocs=rocs)


################################################################################################
# MI
################################################################################################
@query_cache
def query_mi_0(args: Namespace, scan: Scan, context: Vc = Vc.TOOL_HOME) -> Sns:
    """Calculate LOC-weighted Maintainability Index (using latest loc/raw RAW scan)."""
    raw_scan = Scan.get_most_recent(scan.request.project, "radon", "raw")
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
        .where(RadonMi.scan_id == scan.id)
    )
    result = query.dicts().get()
    if result["total_loc"]:
        mi_ = result["weighted_sum"] / result["total_loc"]

    return Sns(mi_metric=score_metric(args, "tools.radon.mi.mean", mi_))


@query_cache
def query_mi_1(args, scan: Scan) -> Sns:
    mi_metric = query_mi_0(args, scan).mi_metric
    raw_scan = Scan.get_most_recent(scan.request.project, "radon", "raw")
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
        .where(RadonMi.scan_id == scan.id)
        .group_by(RadonMi.directory)
        .order_by(RadonMi.directory)
    )
    mi_by_directory = {}
    for row in query.dicts():
        if row["total_loc"]:
            mi_ = row["weighted_sum"] / row["total_loc"]
            mi_by_directory[row["directory"]] = score_metric(args, "tools.radon.mi.mean", mi_)
    return Sns(mi_by_directory=mi_by_directory, mi_metric=mi_metric)


@query_cache
def query_mi_2(args, scan: Scan) -> Sns:
    mi_metric = query_mi_0(args, scan).mi_metric
    query = (
        RadonMi.select()
        .where(RadonMi.scan == scan)
        .order_by(
            RadonMi.directory,
            RadonMi.filename,
        )
        .dicts()
    )
    rows = [Sns(**row_dict) for row_dict in query]
    for row in rows:
        row.metric = score_metric(args, "tools.radon.mi.mean", row.mi)
    return Sns(rows=rows, mi_metric=mi_metric)


@query_cache
def query_mi_h_original(project, last: int = None) -> Sns:
    assert project

    scans = get_scans_for_project_analysis(project, "mi", last=last)
    scan_ids = [scan.id for scan in scans]

    # Alias for the RAW scan to make the query clearer
    rawscan = Scan.alias()

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
            rawscan,
            on=(
                (RadonRaw.scan == rawscan.id)
                & (rawscan.request == Scan.request)
                & (rawscan.tool == "radon")
                & (rawscan.analysis == "raw")
            ),
        )
        .where(RadonMi.scan.in_(scan_ids))
        .group_by(Scan.as_of)
        .order_by(Scan.as_of.desc())
        .dicts()
    )
    rows = {row["timestamp"]: row["mi_weighted"] for row in query.dicts()}
    messages = {row["timestamp"]: row["message"] for row in query.dicts()}

    # Calculate rate of change of last 2 entries..
    timestamps = list(rows.keys())
    roc = 0.00
    if len(timestamps) > 1:
        ts_penultimate, ts_last = sorted(timestamps)[-2:]
        roc = rate_of_change_percentage(rows[ts_penultimate], rows[ts_last])

    return Sns(messages=messages, rows=rows, roc=roc)


@query_cache
def query_mi_h(project, last: int = None) -> Sns:
    assert project

    scans = get_scans_for_project_analysis(project, "mi", last=last)
    scan_ids = [scan.id for scan in scans]

    # Alias for the RAW scan to make the query clearer
    rawscan = Scan.alias()

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
            rawscan,
            on=(
                (RadonRaw.scan == rawscan.id)
                & (rawscan.request == Scan.request)
                & (rawscan.tool == "radon")
                & (rawscan.analysis == "raw")
            ),
        )
        .where(RadonMi.scan.in_(scan_ids))
        .group_by(Scan.as_of)
        .order_by(Scan.as_of.desc())
        .dicts()
    )
    rows = {row["timestamp"]: row["mi_weighted"] for row in query.dicts()}
    messages = {row["timestamp"]: row["message"] for row in query.dicts()}

    # Calculate rate of change of last 2 entries..
    timestamps = list(rows.keys())
    roc = 0.00
    if len(timestamps) > 1:
        ts_penultimate, ts_last = sorted(timestamps)[-2:]
        roc = rate_of_change_percentage(rows[ts_penultimate], rows[ts_last])

    return Sns(messages=messages, rows=rows, roc=roc)


################################################################################################
# CC
################################################################################################
@query_cache
def query_cc_0(args: Namespace, scan: Scan, context: Vc = Vc.TOOL_HOME) -> Sns:
    """Calculate derived radon-cc metric(s)."""
    query = (
        RadonCc.select(
            RadonCc.entity_type.alias("entity_type"),
            fn.AVG(RadonCc.complexity).alias("complexity"),
        )
        .where(RadonCc.scan == scan)
        .group_by(RadonCc.entity_type)
        .order_by(fn.COUNT(RadonCc.id).desc())
    )
    rows = []
    for row in query:
        row.entity_type = RadonCc.entity_type_display(row.entity_type)
        _threshold_type = (
            "tools.radon.cc.classes"  # Allow for different scoring on classes vs. functions/method callables
            if row.entity_type.upper() == "C"  # HARD-CODE!
            else "tools.radon.cc.callables"
        )
        row.metric = score_metric(
            args,
            RadonCc.get_threshold_type(row.entity_type),
            row.complexity,
        )
        rows.append(row)

    return Sns(rows=rows)


@query_cache
def query_cc_1(args: Namespace, scan: Scan) -> Sns:
    query = (
        RadonCc.select(
            RadonCc.directory,
            RadonCc.entity_type,
            fn.AVG(RadonCc.complexity).alias("complexity"),
        )
        .where(RadonCc.scan == scan)
        .group_by(RadonCc.directory, RadonCc.entity_type)
        .order_by(RadonCc.directory, RadonCc.entity_type)
    )
    rows = []
    for row in query:
        row.entity_type = RadonCc.entity_type_display(row.entity_type)
        row.metric = score_metric(
            args,
            RadonCc.get_threshold_type(row.entity_type),
            row.complexity,
        )
        rows.append(row)
    return Sns(rows=rows)


@query_cache
def query_cc_2(args: Namespace, scan: Scan) -> Sns:
    query = (
        RadonCc.select(
            RadonCc.directory,
            RadonCc.filename,
            RadonCc.entity_type,
            fn.AVG(RadonCc.complexity).alias("complexity"),
        )
        .where(RadonCc.scan == scan)
        .group_by(RadonCc.directory, RadonCc.filename, RadonCc.entity_type)
        .order_by(RadonCc.directory, RadonCc.filename, RadonCc.entity_type)
    )
    rows = []
    for row in query:
        row.entity_type = RadonCc.entity_type_display(row.entity_type)
        row.metric = score_metric(
            args,
            RadonCc.get_threshold_type(row.entity_type),
            row.complexity,
        )
        rows.append(row)
    return Sns(rows=rows)


@query_cache
def query_cc_3(args: Namespace, scan: Scan) -> Sns:
    query = (
        RadonCc.select()
        .where(
            RadonCc.scan == scan,
        )
        .order_by(
            RadonCc.directory,
            RadonCc.filename,
            RadonCc.entity_name,
        )
    )
    rows = []
    for row in query:
        row.entity_type = RadonCc.entity_type_display(row.entity_type)
        row.metric = score_metric(
            args,
            RadonCc.get_threshold_type(row.entity_type),
            row.complexity,
        )
        rows.append(row)
    return Sns(rows=rows)


@query_cache
def query_cc_h(project: Project, last: int = None) -> Sns:
    # Step 1: Find the relevant scans for the project (potentially limited)
    scans = get_scans_for_project_analysis(project, "cc", last=last)

    # Step 2: Get aggregated complexity for those scans (fast - no join!)
    scan_id_list = [s.id for s in scans]
    complexity_data = (
        RadonCc.select(
            RadonCc.scan_id,
            RadonCc.entity_type,
            fn.AVG(RadonCc.complexity).alias("avg_complexity"),
        )
        .where(RadonCc.scan_id.in_(scan_id_list))
        .group_by(RadonCc.scan_id, RadonCc.entity_type)
        .dicts()
    )

    # Step 3: Combine in Python (fast - in-memory)
    complexity_by_scan = {}
    for row in complexity_data:
        key = (row["scan"], row["entity_type"])
        complexity_by_scan[key] = row["avg_complexity"]

    # Step 4: Build final result
    query = []
    for scan in scans:
        # Get all entity types for this scan
        for entity_type in set(k[1] for k in complexity_by_scan.keys() if k[0] == scan.id):
            query.append(
                Sns(
                    timestamp=scan.as_of,
                    message=scan.git_commit_message,
                    entity_type=entity_type,
                    complexity=complexity_by_scan.get((scan.id, entity_type), 0),
                ),
            )

    ################################################################################################
    # Transpose (to get timestamps *across* instead of down and calculate grand totals)
    ################################################################################################
    timestamps = list({result.timestamp for result in query})
    messages = {result.timestamp: result.message for result in query}
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

    return Sns(timestamps=timestamps, messages=messages, transposed=transposed, rocs=rocs)


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
