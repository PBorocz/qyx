"""..."""

import logging
from argparse import Namespace
from collections import defaultdict
from types import SimpleNamespace as Sns

import peewee as pw
from peewee import fn

from qyx.constants import ViewContext as Vc
from qyx.tools._models_ import BaseModel, ModelAttribute, Project, Scan
from qyx.tools.common import get_scans_for_project_dimension
from qyx.utils import rate_of_change_percentage
from qyx.utils.caching import query_cache
from qyx.utils.scoring import score_metric


log = logging.getLogger(__name__)


class RadonRaw(BaseModel):
    """Radon "RAW" metric storage."""

    # NOTE: LOC = Blanks + COmments + Multi + SingleComments + SLOC
    # fmt: off
    id              = pw.AutoField()
    scan            = pw.ForeignKeyField(Scan, on_delete="CASCADE")
    directory       = pw.CharField(help_text="eg. src/qyx/") # Relative to project's root!
    filename        = pw.CharField(help_text="eg. foo.py")
    loc             = pw.IntegerField(help_text="Lines of code")
    blank           = pw.IntegerField(help_text="Blank lines")
    comments        = pw.IntegerField(help_text="Comment lines")
    lloc            = pw.IntegerField(help_text="Logical lines of code")
    multi           = pw.IntegerField(help_text="Multi-line strings")
    single_comments = pw.IntegerField(help_text="Single-line comments")
    sloc            = pw.IntegerField(help_text="Source lines of code")
    # fmt: on

    class Meta:
        """Define peewee meta data."""

        table_name = "tool_radon_raw"
        indexes = ((("scan", "directory", "filename"), True),)

    @classmethod
    def attrs(cls) -> tuple[str]:
        """Return the "core" list of attributes (the other 2 are FYI)."""
        return ("loc", "sloc", "comments", "multi", "blank")


class RadonMi(BaseModel):
    """Radon "MI" metric storage."""

    # fmt: off
    id        = pw.AutoField()
    scan      = pw.ForeignKeyField(Scan, on_delete="CASCADE")
    directory = pw.CharField(help_text="eg. src/qyx/") # Relative to project's root!
    filename  = pw.CharField(help_text="eg. foo.py")
    mi        = pw.FloatField(help_text="Maintainability index")
    rank      = pw.CharField(help_text="Grade, ie. A, B, C, etc.")
    # fmt: on

    class Meta:
        """Define peewee meta data."""

        table_name = "tool_radon_mi"
        indexes = ((("scan", "directory", "filename"), True),)


class RadonCc(BaseModel):
    """Radon "CC" metric storage."""

    # fmt: off
    id            = pw.AutoField()
    scan          = pw.ForeignKeyField(Scan, on_delete="CASCADE")
    directory     = pw.CharField(help_text="eg. src/qyx/") # Relative to project's root!
    filename      = pw.CharField(help_text="eg. foo.py")
    entity_type   = pw.CharField(help_text="Function, Method or Class)")
    entity_name   = pw.CharField(help_text="main, <class>.method, etc.")
    line_start    = pw.IntegerField()
    line_end      = pw.IntegerField()
    column_offset = pw.IntegerField()
    rank          = pw.CharField(help_text="Complexity grade, ie. A, B, C...")
    complexity    = pw.IntegerField(help_text="Raw complexity score")
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

        table_name = "tool_radon_cc"
        indexes = (
            # Uniqueness criteria
            (("scan", "directory", "filename", "entity_type", "entity_name", "line_start", "line_end"), True),
            # Optimisation for joining + grouping by entity_type
            (("scan", "entity_type"), False),
        )


class RadonHal(BaseModel):
    """Radon "HAL" metric storage."""

    # fmt: off
    id                 = pw.AutoField()
    scan               = pw.ForeignKeyField(Scan, on_delete="CASCADE")
    directory          = pw.CharField(help_text="eg. src/qyx/") # Relative to project's root!
    filename           = pw.CharField(help_text="eg. foo.py")
    h1		       = pw.IntegerField () # See below for descriptions...
    h2		       = pw.IntegerField ()
    N1		       = pw.IntegerField ()
    N2		       = pw.IntegerField ()
    program_vocabulary = pw.IntegerField ()
    program_length     = pw.IntegerField ()
    calculated_length  = pw.FloatField   ()
    volume             = pw.FloatField   ()
    difficulty         = pw.FloatField   ()
    effort             = pw.FloatField   ()
    time               = pw.FloatField   ()
    bugs               = pw.FloatField   ()
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

        table_name = "tool_radon_hal"
        indexes = ((("scan", "directory", "filename"), True),)


class RadonHalFunction(BaseModel):
    """Radon "HAL" Function metric storage."""

    # fmt: off
    scan              = pw.ForeignKeyField(Scan, backref="radon_hal_function_scan", on_delete="CASCADE")
    radon_hal         = pw.ForeignKeyField(RadonHal, backref="radon_hal_function", on_delete="CASCADE")
    name              = pw.CharField(help_text="function name")
    h1		      = pw.IntegerField(help_text="Total distinct operators")
    h2		      = pw.IntegerField(help_text="Total distinct operands")
    N1		      = pw.IntegerField(help_text="Total operators in file")
    N2		      = pw.IntegerField(help_text="Total operands in file")
    program_vocabulary= pw.IntegerField(help_text="Total vocabulary (h = h1 + h2)")
    program_length    = pw.IntegerField(help_text="Total length (N = N1 + N2)")
    calculated_length = pw.IntegerField(help_text="(see wikipedia page!)")
    volume            = pw.FloatField(help_text="Total volume (V = N log2 h)")
    difficulty        = pw.FloatField(help_text="Mean difficulty across functions (D = ((h1/2) * (N2/h2)))")
    effort            = pw.FloatField(help_text="Total effort (E = D * V)")
    time              = pw.FloatField(help_text="Total time (T = (E / 18) in seconds)")
    bugs              = pw.FloatField(help_text="Estimated bugs for file (B = V / 3000)")
    # fmt:

    class Meta:
        """Define peewee meta data."""

        table_name = "tool_radon_hal_function"
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
def query_raw_h(project: Project, dimension: str = "raw", last: int = None) -> Sns:
    scans = get_scans_for_project_dimension(project, dimension, last=last)

    ################################################################################################
    # Look through to the internal summary.
    ################################################################################################
    rows = list()
    for scan in scans:
        if not scan.summary:
            continue
        row = Sns(timestamp=scan.as_of, git_commit_message=scan.git_commit_message)
        for attr in RadonRaw.attrs():
            setattr(row, attr, scan.summary.get(attr, 0))
        rows.append(row)
    timestamps = [row.timestamp for row in rows]
    messages = {row.timestamp: row.git_commit_message for row in rows}

    ################################################################################################
    # Transpose (to get timestamps *across* instead of down and calculate grand totals)
    ################################################################################################
    transposed = defaultdict(lambda: defaultdict(dict))
    for row in rows:
        total = 0
        for attr in RadonRaw.attrs():
            lines = int(getattr(row, attr))
            transposed[attr][row.timestamp] = lines
            total += lines  # Calculate grand totals for each timestamp as we go

    # Calculate rate of change of last 2 entries..
    rocs = dict()
    for attr in RadonRaw.attrs():
        l_timestamps = sorted(transposed[attr].keys())
        if len(l_timestamps) > 1:
            ts_penultimate, ts_last = l_timestamps[-2:]
            rocs[attr] = rate_of_change_percentage(transposed[attr][ts_penultimate], transposed[attr][ts_last])
        else:
            rocs[attr] = 0.0

    if len(timestamps) > 1:
        ts_penultimate, ts_last = sorted(timestamps)[-2:]
        roc_gt = rate_of_change_percentage(transposed["loc"][ts_penultimate], transposed["loc"][ts_last])
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
    raw = query_raw_0(args, scan=Scan.get_latest(scan.request.project, "radon", "raw"))

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
def query_hal_h(project: Project = None, dimension: str = "hal", last: int = None) -> Sns:
    scans = get_scans_for_project_dimension(project, dimension, last=last)

    ################################################################################################
    # Look through to the internal summary.
    ################################################################################################
    rows = list()
    for scan in scans:
        if not scan.summary:
            continue
        row = Sns(timestamp=scan.as_of, git_commit_message=scan.git_commit_message)
        for o_attr in RadonHal.attrs():
            setattr(row, o_attr.name, scan.summary.get(o_attr.name, 0))
        rows.append(row)
    timestamps = [row.timestamp for row in rows]
    messages = {row.timestamp: row.git_commit_message for row in rows}

    ################################################################################################
    # Transpose (to get timestamps *across* instead of down and calculate grand totals)
    ################################################################################################
    transposed = defaultdict(lambda: defaultdict(dict))
    for row in rows:
        total = 0
        for attr in RadonHal.attrs():
            value = getattr(row, attr.name)
            transposed[attr.name][row.timestamp] = value
            total += value  # Calculate grand totals for each timestamp as we go

    # Calculate rate of change of last 2 entries..
    rocs = dict()
    for attr in RadonHal.attrs():
        l_timestamps = sorted(transposed[attr.name].keys())
        if len(l_timestamps) > 1:
            ts_penultimate, ts_last = l_timestamps[-2:]
            rocs[attr.name] = rate_of_change_percentage(
                transposed[attr.name][ts_penultimate],
                transposed[attr.name][ts_last],
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
    raw_scan = Scan.get_latest(scan.request.project, "radon", "raw")
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
    raw_scan = Scan.get_latest(scan.request.project, "radon", "raw")
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
def query_mi_h(project, dimension: str = "mi", last: int = None) -> Sns:
    scans = get_scans_for_project_dimension(project, dimension, last=last)

    ################################################################################################
    # Look through to the internal summary.
    ################################################################################################
    rows = {}
    for scan in scans:
        if not scan.summary:
            continue
        rows[scan.as_of] = Sns(
            timestamp=scan.as_of,
            git_commit_message=scan.git_commit_message,
            maintainability_index=scan.summary.get("maintainability_index", 0.0),
        )
    timestamps = sorted(list(rows.keys()))
    messages = {row.timestamp: row.git_commit_message for row in rows.values()}

    # Calculate rate of change of last 2 entries..
    roc = 0.00
    if len(timestamps) > 1:
        ts_penultimate, ts_last = timestamps[-2:]
        roc = rate_of_change_percentage(
            rows[ts_penultimate].maintainability_index,
            rows[ts_last].maintainability_index,
        )

    return Sns(rows=rows, timestamps=timestamps, messages=messages, roc=roc)


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
def query_cc_h(project: Project, dimension: str = "cc", last: int = None) -> Sns:
    scans = get_scans_for_project_dimension(project, dimension, last=last)

    ################################################################################################
    # Transpose (to get timestamps *across* instead of down and calculate grand totals)
    ################################################################################################
    timestamps = [scan.as_of for scan in scans]
    messages = {scan.as_of: scan.git_commit_message for scan in scans}

    transposed = defaultdict(lambda: defaultdict(dict))
    for scan in scans:
        if not scan.summary:
            continue
        if not (d_mean_complexity := scan.summary.get("mean_complexity")):
            continue
        for entity_type, complexity in d_mean_complexity.items():
            transposed[entity_type][scan.as_of] = complexity

    # Calculate rate of change of last 2 entries for each entity type
    rocs = dict()
    for entity_type, values_by_timestamp in transposed.items():
        l_timestamps = sorted(values_by_timestamp.keys())
        if len(l_timestamps) > 1:
            ts_penultimate, ts_last = l_timestamps[-2:]
            rocs[entity_type] = rate_of_change_percentage(
                values_by_timestamp[ts_penultimate],
                values_by_timestamp[ts_last],
            )

    return Sns(timestamps=timestamps, messages=messages, transposed=transposed, rocs=rocs)
