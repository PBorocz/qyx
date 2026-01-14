"""..."""

import logging
from argparse import Namespace
from collections import defaultdict
from typing import Any

from peewee import fn, CharField, FloatField, IntegerField, ForeignKeyField

from mq.tools.base import BaseModel, BaseResultsModel, Project, Request, Scan
from mq.utils import rate_of_change_percentage


log = logging.getLogger(__name__)


class RadonRaw(BaseResultsModel):
    """Radon "RAW" metric storage."""

    # fmt: off
    loc             = IntegerField(help_text="Lines of code")
    lloc            = IntegerField(help_text="Logical lines of code")
    sloc            = IntegerField(help_text="Source lines of code")
    comments        = IntegerField(help_text="Comment lines")
    multi           = IntegerField(help_text="Multi-line strings")
    blank           = IntegerField(help_text="Blank lines")
    single_comments = IntegerField(help_text="Single-line comments")
    # fmt: on

    class Meta:
        """Define peewee meta data."""

        table_name = "radon_raw"
        indexes = ((("scan", "directory", "filename"), True),)


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
    entity_type   = CharField(help_text="F, M or C (function, method or class)")
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
            return "D"  # more than moderate - more complex block
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
        """Return a list of the attributes/metrics for the model (display, attr, type)."""
        # fmt: off
        return (
            ("Estimated Bugs For File (V / 3000)"          , "bugs"               , "float"),
            ("Total Time (E / 18 seconds)"                 , "time"               , "float"),
            ("Total Effort (E = D * V)"                    , "effort"             , "float"),
            ("Mean Difficulty (D = ((h1/2) * (N2/h2)))" , "difficulty"         , "float"),
            ("Volume (V = N log2 h))"                          , "volume"             , "float"),
            ("Calculated Length"                           , "calculated_length"  , "float"),
            ("Program Length (N = N1 + N2)"                , "program_length"     , "int"  ),
            ("Program Vocabulary (h = h1 + h2)"            , "program_vocabulary" , "int"  ),
            ("Total Operands in File (N2)"                 , "N2"                 , "int"  ),
            ("Total Operators in File (N1)"                , "N1"                 , "int"  ),
            ("Total Distinct Operands (h2)"                , "h2"                 , "int"  ),
            ("Total Distinct Operators (h1)"               , "h1"                 , "int"  ),
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
def query_raw(level: str = "0", scan: Scan = None, project: Project = None, last: int = None) -> Any:
    match level.lower():
        case "0":
            return _query_raw_0(scan)
        case "1":
            return _query_raw_1(scan)
        case "2":
            return _query_raw_2(scan)
        case "h":
            return _query_raw_h(project, last)
        case _:
            raise RuntimeError(f"Sorry, invalid query level encountered! {level}")


def _query_raw_0(scan: Scan) -> Any:
    return (
        RadonRaw.select(
            fn.SUM(RadonRaw.loc).alias("loc"),
            fn.SUM(RadonRaw.lloc).alias("lloc"),
            fn.SUM(RadonRaw.sloc).alias("sloc"),
            fn.SUM(RadonRaw.comments).alias("comments"),
            fn.SUM(RadonRaw.multi).alias("multi"),
            fn.SUM(RadonRaw.blank).alias("blank"),
            fn.SUM(RadonRaw.single_comments).alias("single_comments"),
        )
        .where(RadonRaw.scan == scan)
        .first()
    )


def _query_raw_1(scan: Scan) -> Any:
    raw_attrs = ("loc", "lloc", "sloc", "comments", "multi", "blank", "single_comments")
    rows = (
        RadonRaw.select(
            RadonRaw.directory,
            fn.SUM(RadonRaw.loc).alias("loc"),
            fn.SUM(RadonRaw.lloc).alias("lloc"),
            fn.SUM(RadonRaw.sloc).alias("sloc"),
            fn.SUM(RadonRaw.comments).alias("comments"),
            fn.SUM(RadonRaw.multi).alias("multi"),
            fn.SUM(RadonRaw.blank).alias("blank"),
            fn.SUM(RadonRaw.single_comments).alias("single_comments"),
        )
        .where(RadonRaw.scan == scan)
        .group_by(RadonRaw.directory)
        .order_by(RadonRaw.directory)
    )

    # Calculate totals
    totals = defaultdict(int)
    for row in rows:
        for attr in raw_attrs:
            totals[attr] += getattr(row, attr)
    return rows, totals


def _query_raw_2(scan: Scan) -> Any:
    return RadonRaw.select().where(RadonRaw.scan == scan).order_by(RadonRaw.directory, RadonRaw.filename)


def _query_raw_h(project: Project, last: int = None) -> Any:
    # FIXME: Refactor to make this a "common" query given the number of places we use it:
    raw_attrs = ("loc", "lloc", "sloc", "comments", "multi", "blank", "single_comments")
    scans = (
        Scan.select()
        .where(
            Request.project == project,
            Scan.tool == "radon",
            Scan.analysis == "raw",
        )
        .join(Request)
        .order_by(Scan.as_of.desc())
    )
    if last:
        scans = scans.limit(last)

    query = (
        RadonRaw.select(
            Scan.as_of.alias("timestamp"),
            fn.SUM(RadonRaw.loc).alias("loc"),
            fn.SUM(RadonRaw.lloc).alias("lloc"),
            fn.SUM(RadonRaw.sloc).alias("sloc"),
            fn.SUM(RadonRaw.comments).alias("comments"),
            fn.SUM(RadonRaw.multi).alias("multi"),
            fn.SUM(RadonRaw.blank).alias("blank"),
            fn.SUM(RadonRaw.single_comments).alias("single_comments"),
        )
        .join(Scan)
        .where(Scan.id.in_(scans))
        .group_by(Scan.as_of)
        .order_by(Scan.as_of)
        .objects()
    )

    ################################################################################################
    # Transpose (to get timestamps *across* instead of down and calculate grand totals)
    ################################################################################################
    timestamps = [result.timestamp for result in query]
    transposed = defaultdict(lambda: defaultdict(dict))
    for result in query:
        total = 0
        for attr in raw_attrs:
            lines = int(getattr(result, attr))
            transposed[attr][result.timestamp] = lines
            total += lines  # Calculate grand totals for each timestamp as we go

    # Calculate rate of change of last 2 entries..
    rocs = dict()
    for attr in raw_attrs:
        if len(timestamps) > 1:
            rocs[attr] = rate_of_change_percentage(
                transposed[attr][timestamps[-2]],
                transposed[attr][timestamps[-1]],
            )
        else:
            rocs[attr] = 0.0

    if len(timestamps) > 1:
        roc_gt = rate_of_change_percentage(
            transposed["loc"][timestamps[-2]],
            transposed["loc"][timestamps[-1]],
        )
    else:
        roc_gt = 0.0

    return timestamps, transposed, rocs, roc_gt


################################################################################################
# HAL
################################################################################################
def query_hal(level: str = "0", scan: Scan = None, project: Project = None, last: int = None) -> Any:
    match level.lower():
        case "0":
            return _query_hal_0(scan)
        case "1":
            return _query_hal_1(scan)
        case "2":
            return _query_hal_2(scan)
        case "3":
            return _query_hal_3(scan)
        case "d":
            return _query_hal_d(project, scan)
        case "h":
            return _query_hal_h(project, last)
        case _:
            raise RuntimeError(f"Sorry, invalid query level requested {level=}")


def _query_hal_0(scan: Scan) -> Any:
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


def _query_hal_1(scan: Scan) -> Any:
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
    for _, attr, _ in RadonHal.attrs():
        values = [getattr(row, attr) for row in rows]
        mean_means[attr] = sum(values) / len(values) if values else None

    return rows, mean_means


def _query_hal_2(scan: Scan) -> Any:
    rows = RadonHal.select().where(RadonHal.scan == scan).order_by(RadonHal.directory, RadonHal.filename)

    # Calculate means
    means = {}
    for _, attr, _ in RadonHal.attrs():
        values = [getattr(row, attr) for row in rows]
        means[attr] = sum(values) / len(values) if values else None
    return rows, means


def _query_hal_3(scan: Scan) -> Any:
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
    for _, attr, _ in RadonHal.attrs():
        values = [getattr(row, attr) for row in rows]
        means[attr] = sum(values) / len(values) if values else None

    return rows, means


def _query_hal_h(project: Project = None, last: int = 5) -> Any:
    scans = (
        Scan.select()
        .where(
            Request.project == project,
            Scan.tool == "radon",
            Scan.analysis == "hal",
        )
        .join(Request)
        .order_by(Scan.as_of.desc())
    )
    if last:
        scans = scans.limit(last)

    query = (
        RadonHal.select(
            Scan.as_of.alias("timestamp"),
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

    ################################################################################################
    # Transpose (to get timestamps *across* instead of down and calculate grand totals)
    ################################################################################################
    timestamps = [result.timestamp for result in query]
    transposed = defaultdict(lambda: defaultdict(dict))
    for result in query:
        total = 0
        for _, attr, _ in RadonHal.attrs():
            value = getattr(result, attr)
            transposed[attr][result.timestamp] = value
            total += value  # Calculate grand totals for each timestamp as we go

    # Calculate rate of change of last 2 entries..
    rocs = dict()
    for _, attr, _ in RadonHal.attrs():
        if len(timestamps) > 1:
            rocs[attr] = rate_of_change_percentage(
                transposed[attr][timestamps[-2]],
                transposed[attr][timestamps[-1]],
            )
        else:
            rocs[attr] = 0.00

    return timestamps, transposed, rocs


def _query_hal_d(project: Project, scan: Scan):
    """Calculate derived radon-hal metric(s)."""
    raw_scan = Scan.get_most_recent(project, "radon", "raw")
    raw = _query_raw_0(scan=raw_scan)
    row = _query_hal_0(scan)
    row = _derived_hal_bugs(raw, row)
    row = _derived_hal_effort(raw, row)
    row = _derived_hal_difficulty(row)
    row = _derived_hal_composite(row)
    return row


def _derived_hal_composite(row):
    difficulty_score = max(0, 100 - (row.difficulty_d.score / 40) * 100)
    bugs_score = max(0, 100 - (row.bugs_d.score / 1.0) * 100)
    effort_score = max(0, 100 - (row.effort_d.score / 1000) * 100)

    # Weighted average (bugs matter most!)
    composite = bugs_score * 0.5 + difficulty_score * 0.3 + effort_score * 0.2

    if composite >= 80:
        grade, color = "A", "#22c55e"
    elif composite >= 70:
        grade, color = "B", "#84cc16"
    elif composite >= 60:
        grade, color = "C", "#eab308"
    elif composite >= 50:
        grade, color = "D", "#f97316"
    else:
        grade, color = "F", "#ef4444"
    row.composite_d = Namespace(score=composite, grade=grade, color=color)
    return row


def _derived_hal_bugs(raw_scan, row):
    """Calculate score of Halstead effort per line of code."""
    bugs_per_kloc = (row.bugs / raw_scan.loc) * 1000
    if bugs_per_kloc <= 0.1:
        grade, color = "A", "#22c55e"  # < 0.1 bugs/KLOC
    elif bugs_per_kloc <= 0.3:
        grade, color = "B", "#84cc16"  # 0.1-0.3 bugs/KLOC
    elif bugs_per_kloc <= 0.6:
        grade, color = "C", "#eab308"  # 0.3-0.6 bugs/KLOC
    elif bugs_per_kloc <= 1.0:
        grade, color = "D", "#f97316"  # 0.6-1.0 bugs/KLOC
    else:
        grade, color = "F", "#ef4444"  # > 1 bug/KLOC
    row.bugs_d = Namespace(score=bugs_per_kloc, grade=grade, color=color)
    return row


def _derived_hal_effort(raw_scan, row):
    """Calculate score of Halstead effort per line of code."""
    effort_per_loc = row.effort / raw_scan.loc

    if effort_per_loc <= 100:
        grade, color = "A", "#22c55e"  # Low effort
    elif effort_per_loc <= 300:
        grade, color = "B", "#84cc16"  # Moderate effort
    elif effort_per_loc <= 600:
        grade, color = "C", "#eab308"  # High effort
    elif effort_per_loc <= 1000:
        grade, color = "D", "#f97316"  # Very high effort
    else:
        grade, color = "F", "#ef4444"  # Extreme effort
    row.effort_d = Namespace(score=effort_per_loc, grade=grade, color=color)
    return row


def _derived_hal_difficulty(row):
    """Calculate score of Halstead difficulty metric."""
    if row.difficulty <= 5:
        grade, color = "A", "#22c55e"  # Very easy
    elif row.difficulty <= 10:
        grade, color = "B", "#84cc16"  # Easy
    elif row.difficulty <= 20:
        grade, color = "C", "#eab308"  # Moderate
    elif row.difficulty <= 40:
        grade, color = "D", "#f97316"  # Difficult
    else:
        grade, color = "F", "#ef4444"  # Very difficult
    row.difficulty_d = Namespace(score=row.difficulty, grade=grade, color=color)
    return row


################################################################################################
# MI
################################################################################################
def query_mi(level: str = "0", scan: Scan = None, project: Project = None, last: int = None) -> Any:
    match level.lower():
        case "0":
            return _query_mi_0(scan)
        case "1":
            return _query_mi_1(scan)
        case "2":
            return _query_mi_2(scan)
        case "d":
            return _query_mi_d(scan)
        case "h":
            return _query_mi_h(project, last)
        case _:
            raise RuntimeError(f"Sorry, invalid query level encountered! {level}")


def _query_mi_0(scan: Scan) -> Any:
    # TODO: Should this be weighted by number of lines in file?
    row = RadonMi.select(fn.AVG(RadonMi.mi).alias("mi_mean")).where(RadonMi.scan == scan).get()
    return row


def _query_mi_1(scan: Scan) -> Any:
    rows = (
        RadonMi.select(RadonMi.directory, fn.AVG(RadonMi.mi).alias("mi_mean"))
        .where(RadonMi.scan == scan)
        .order_by(fn.AVG(RadonMi.mi).asc(), RadonMi.directory)
        .group_by(RadonMi.directory)
    )

    # Calculate the mean mean maintainability index
    mi_mean_s = [row.mi_mean for row in rows]
    if mi_mean_s:
        mean_mi_mean = sum(mi_mean_s) / len(mi_mean_s)
        mean_mi_mean_footer = f"{mean_mi_mean:.2f}"
        show_footer = True
    else:
        mean_mi_mean_footer = ""
        show_footer = False
    return rows, mean_mi_mean, mean_mi_mean_footer, show_footer


def _query_mi_2(scan: Scan) -> Any:
    rows = RadonMi.select().where(RadonMi.scan == scan).order_by(RadonMi.mi.asc(), RadonMi.directory, RadonMi.filename)
    # Calculate the average maintainability index
    mi_s = [row.mi for row in rows]
    if mi_s:
        avg_mi = sum(mi_s) / len(mi_s)
        avg_footer = f"{avg_mi:.2f}"
        show_footer = True
    else:
        avg_footer = ""
        show_footer = False
    return rows, avg_footer, show_footer


def _query_mi_h(project, last: int = 5) -> Any:
    assert project
    scans = (
        Scan.select(Scan.id)
        .where(
            Request.project == project,
            Scan.tool == "radon",
            Scan.analysis == "mi",
        )
        .join(Request)
        .order_by(Scan.as_of.desc())
    )
    if last:
        scans = scans.limit(last)

    scan_ids = [scan.id for scan in scans]

    query = (
        RadonMi.select(
            Scan.as_of.alias("timestamp"),
            fn.AVG(RadonMi.mi).alias("mi_mean"),
        )
        .where(
            RadonMi.scan.in_(scan_ids),
        )
        .join(Scan)
        .group_by(Scan.as_of)
        .order_by(Scan.as_of.desc())
        .objects()
    )

    ################################################################################################
    # Transpose (to get timestamps *across* instead of down and calculate grand totals)
    ################################################################################################
    timestamps = [result.timestamp for result in query]
    transposed = defaultdict(lambda: defaultdict(dict))
    for result in query:
        transposed["mi"][result.timestamp] = result.mi_mean

    # Calculate rate of change of last 2 entries..
    if len(timestamps) > 1:
        roc = rate_of_change_percentage(transposed["mi"][timestamps[-1]], transposed["mi"][timestamps[-2]])
    else:
        roc = 0.00

    return timestamps, transposed, roc


def _query_mi_d(scan: Scan):
    """Calculate derived radon-mi metric(s)."""
    result = _query_mi_0(scan)
    if result.mi_mean >= 85:
        grade, color = "A", "#22c55e"  # green - Highly maintainable
    elif result.mi_mean >= 75:
        grade, color = "B", "#84cc16"  # lime - Good
    elif result.mi_mean >= 65:
        grade, color = "C", "#eab308"  # yellow - Moderate
    elif result.mi_mean >= 50:
        grade, color = "D", "#f97316"  # orange - Needs work
    else:
        grade, color = "F", "#ef4444"  # red - Difficult to maintain
    result.mi_d = Namespace(score=result.mi_mean, grade=grade, color=color)

    return result


def query_cc(level: str = "0", scan: Scan = None, project: Project = None, last: int = None) -> Any:
    match level.lower():
        case "0":
            return _query_cc_0(scan)
        case "1":
            return _query_cc_1(scan)
        case "2":
            return _query_cc_2(scan)
        case "3":
            return _query_cc_3(scan)
        case "d":
            return _query_cc_d(scan)
        case "h":
            return _query_cc_h(project, last)
        case _:
            raise RuntimeError(f"Sorry, invalid query level encountered! {level}")


################################################################################################
# CC
################################################################################################
def _query_cc_0(scan: Scan) -> Any:
    return (
        RadonCc.select(
            RadonCc.entity_type.alias("entity_type"),
            fn.AVG(RadonCc.complexity).alias("mean_complexity"),
        )
        .where(RadonCc.scan == scan)
        .group_by(RadonCc.entity_type)
        .order_by(fn.COUNT(RadonCc.id).desc())
    )


def _query_cc_1(scan: Scan) -> Any:
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


def _query_cc_2(scan: Scan) -> Any:
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


def _query_cc_3(scan: Scan) -> Any:
    return (
        RadonCc.select().where(RadonCc.scan == scan).order_by(RadonCc.directory, RadonCc.filename, RadonCc.entity_name)
    )


def _query_cc_h(project: Project, last: int = None) -> Any:
    scans = (
        Scan.select()
        .where(
            Request.project == project,
            Scan.tool == "radon",
            Scan.analysis == "cc",
        )
        .join(Request)
        .order_by(Scan.as_of.desc())
    )
    if last:
        scans = scans.limit(last)

    query = (
        RadonCc.select(
            Scan.as_of.alias("timestamp"),
            RadonCc.entity_type,
            fn.AVG(RadonCc.complexity).alias("complexity"),
        )
        .join(Scan)
        .where(Scan.id.in_(scans))
        .group_by(Scan.as_of, RadonCc.entity_type)
        .order_by(Scan.as_of)
        .objects()
    )

    ################################################################################################
    # Transpose (to get timestamps *across* instead of down and calculate grand totals)
    ################################################################################################
    timestamps = list({result.timestamp for result in query})
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

    return timestamps, transposed, rocs


def _query_cc_d(scan: Scan):  # noqa: C901
    """Calculate derived radon-cc metric(s)."""
    # Standards reference:
    # - McCabe (1976)*: CC > 10 indicates high risk
    # - NIST          : CC > 15 is concerning, > 20 is dangerous
    results = _query_cc_0(scan)
    for result in results:
        match result.entity_type.lower():
            case "class":
                if result.mean_complexity <= 20:
                    grade, color = "A", "#22c55e"  # Simple
                elif result.mean_complexity <= 40:
                    grade, color = "B", "#84cc16"  # Low risk
                elif result.mean_complexity <= 80:
                    grade, color = "C", "#eab308"  # Moderate
                elif result.mean_complexity <= 150:
                    grade, color = "D", "#f97316"  # Complex
                else:
                    grade, color = "F", "#ef4444"  # Untestable
            case _:
                # Functions and methods...
                if result.mean_complexity <= 5:
                    grade, color = "A", "#22c55e"  # Simple
                elif result.mean_complexity <= 10:
                    grade, color = "B", "#84cc16"  # Low risk
                elif result.mean_complexity <= 20:
                    grade, color = "C", "#eab308"  # Moderate
                elif result.mean_complexity <= 50:
                    grade, color = "D", "#f97316"  # Complex
                else:
                    grade, color = "F", "#ef4444"  # Untestable

        result.cc_d = Namespace(score=result.mean_complexity, grade=grade, color=color)

    return results
