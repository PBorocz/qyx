"""..."""

from argparse import Namespace
from collections import defaultdict
from typing import Any

from peewee import fn, CharField, FloatField, IntegerField, ForeignKeyField

from mq.tools.base import BaseModel, BaseResultsModel, Project, Request, Scan
from mq.utils import rate_of_change_percentage


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
            ("Average Difficulty (D = ((h1/2) * (N2/h2)))" , "difficulty"         , "float"),
            ("Volume (N log2 h))"                          , "volume"             , "float"),
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
    difficulty        = FloatField(help_text="Average difficulty across functions (D = ((h1/2) * (N2/h2)))")
    effort            = FloatField(help_text="Total effort (E = D * V)")
    time              = FloatField(help_text="Total time (T = (E / 18) in seconds)")
    bugs              = FloatField(help_text="Estimated bugs for file (B = V / 3000)")
    # fmt:

    class Meta:
        """Define peewee meta data."""

        table_name = "radon_hal_function"
        indexes = ((("radon_hal", "name"), True),)


################################################################################################
# Queries..
################################################################################################
def query_raw(args: Namespace, level: str = "0", scan: Scan = None, project: Project = None) -> Any:
    match level.lower():
        case "0":
            return query_raw_0(args, level, scan, project)
        case "1":
            return query_raw_1(args, level, scan, project)
        case "2":
            return query_raw_2(args, level, scan, project)
        case "h" | "history":
            return query_raw_h(args, level, scan, project)
        case _:
            raise RuntimeError(f"Sorry, invalid query level encountered! {level}")


def query_raw_0(args: Namespace, level: str = "0", scan: Scan = None, project: Project = None) -> Any:
    return RadonRaw.select(
        fn.SUM(RadonRaw.loc).alias("loc"),
        fn.SUM(RadonRaw.lloc).alias("lloc"),
        fn.SUM(RadonRaw.sloc).alias("sloc"),
        fn.SUM(RadonRaw.comments).alias("comments"),
        fn.SUM(RadonRaw.multi).alias("multi"),
        fn.SUM(RadonRaw.blank).alias("blank"),
        fn.SUM(RadonRaw.single_comments).alias("single_comments"),
    ).where(RadonRaw.scan == scan)


def query_raw_1(args: Namespace, level: str = "0", scan: Scan = None, project: Project = None) -> Any:
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


def query_raw_2(args: Namespace, level: str = "0", scan: Scan = None, project: Project = None) -> Any:
    return RadonRaw.select().where(RadonRaw.scan == scan).order_by(RadonRaw.directory, RadonRaw.filename)


def query_raw_h(args: Namespace, level: str = "0", scan: Scan = None, project: Project = None) -> Any:
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
        .limit(args.options.last)
    )

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


def query_hal(args: Namespace, level: str = "0", scan: Scan = None, project: Project = None) -> Any:
    match level.lower():
        case "0":
            return query_hal_0(args, level, scan, project)
        case "1":
            return query_hal_1(args, level, scan, project)
        case "2":
            return query_hal_2(args, level, scan, project)
        case "3":
            return query_hal_3(args, level, scan, project)
        case "h":
            return query_hal_h(args, level, scan, project)
        case _:
            raise RuntimeError(f"Sorry, invalid query level requested {level=}")


def query_hal_0(args: Namespace, level: str = "0", scan: Scan = None, project: Project = None) -> Any:
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


def query_hal_1(args: Namespace, level: str = "0", scan: Scan = None, project: Project = None) -> Any:
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


def query_hal_2(args: Namespace, level: str = "0", scan: Scan = None, project: Project = None) -> Any:
    rows = RadonHal.select().where(RadonHal.scan == scan).order_by(RadonHal.directory, RadonHal.filename)

    # Calculate means
    means = {}
    for _, attr, _ in RadonHal.attrs():
        values = [getattr(row, attr) for row in rows]
        means[attr] = sum(values) / len(values) if values else None
    return rows, means


def query_hal_3(args: Namespace, level: str = "0", scan: Scan = None, project: Project = None) -> Any:
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


def query_hal_h(args: Namespace, level: str = "0", scan: Scan = None, project: Project = None) -> Any:
    scans = (
        Scan.select()
        .where(
            Request.project == project,
            Scan.tool == "radon",
            Scan.analysis == "hal",
        )
        .join(Request)
        .order_by(Scan.as_of.desc())
        .limit(args.options.last)
    )

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


def query_mi(args: Namespace, level: str = "0", scan: Scan = None, project: Project = None) -> Any:
    match level.lower():
        case "0":
            return RadonMi.select(fn.AVG(RadonMi.mi).alias("mi_mean")).where(RadonMi.scan == scan).get()

        case "1":
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

        case "2":
            rows = (
                RadonMi.select()
                .where(RadonMi.scan == scan)
                .order_by(RadonMi.mi.asc(), RadonMi.directory, RadonMi.filename)
            )
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

        case "h" | "history":
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
                .limit(args.options.last)
            )
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

        case _:
            raise RuntimeError(f"Sorry, invalid query level encountered! {level}")


def query_cc(args: Namespace, level: str = "0", scan: Scan = None, project: Project = None) -> Any:
    match level.lower():
        case "0":
            return (
                RadonCc.select(
                    RadonCc.entity_type.alias("entity_type"),
                    fn.AVG(RadonCc.complexity).alias("mean_complexity"),
                )
                .where(RadonCc.scan == scan)
                .group_by(RadonCc.entity_type)
                .order_by(fn.COUNT(RadonCc.id).desc())
            )

        case "1":
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

        case "2":
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

        case "3":
            return (
                RadonCc.select()
                .where(RadonCc.scan == scan)
                .order_by(RadonCc.directory, RadonCc.filename, RadonCc.entity_name)
            )

        case "h":
            scans = (
                Scan.select()
                .where(
                    Request.project == project,
                    Scan.tool == "radon",
                    Scan.analysis == "cc",
                )
                .join(Request)
                .order_by(Scan.as_of.desc())
                .limit(args.options.last)
            )
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

        case _:
            raise RuntimeError(f"Sorry, invalid query level encountered! {level}")
