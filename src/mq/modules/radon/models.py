"""..."""

from argparse import Namespace
from collections import defaultdict
from typing import Any

from peewee import fn, CharField, FloatField, IntegerField, ForeignKeyField

from mq.modules.base import BaseModel, BaseModuleModel, Project, Run
from mq.modules.radon import MODULE
from mq.utils import rate_of_change_percentage


class RadonRaw(BaseModuleModel):
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
        indexes = ((("run", "dir", "filename"), True),)


class RadonMi(BaseModuleModel):
    """Radon "MI" metric storage."""

    # fmt: off
    mi   = FloatField(help_text="Maintainability index")
    rank = CharField(help_text="Grade, ie. A, B, C, etc.")
    # fmt: on

    class Meta:
        """Define peewee meta data."""

        table_name = "radon_mi"
        indexes = ((("run", "dir", "filename"), True),)


class RadonCc(BaseModuleModel):
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

    class Meta:
        """Define peewee meta data."""

        table_name = "radon_cc"
        indexes = ((("run", "dir", "filename", "entity_type", "entity_name"), True),)


class RadonHal(BaseModuleModel):
    """Radon "HAL" metric storage."""

    # fmt: off
    h1		       = IntegerField(help_text="Total distinct operators")
    h2		       = IntegerField(help_text="Total distinct operands")
    N1		       = IntegerField(help_text="Total operators in file")
    N2		       = IntegerField(help_text="Total operands in file")
    program_vocabulary = IntegerField(help_text="Total vocabulary (h = h1 + h2)")
    program_length     = IntegerField(help_text="Total length (N = N1 + N2)")
    calculated_length  = IntegerField(help_text="(see wikipedia page!)")
    volume             = FloatField(help_text="Total volume (V = N log2 h)")
    difficulty         = FloatField(help_text="Average difficulty across functions (D = ((h1/2) * (N2/h2)))")
    effort             = FloatField(help_text="Total effort (E = D * V)")
    time               = FloatField(help_text="Total time (T = (E / 18) in seconds)")
    bugs               = FloatField(help_text="Estimated bugs for file (B = V / 3000)")
    # fmt:

    @classmethod
    def attributes(cls) -> list[str]:
        """Return a list of the attributes/metrics for the model."""
        return (
            "h1",
            "h2",
            "N1",
            "N2",
            "program_vocabulary",
            "program_length",
            "calculated_length",
            "volume",
            "difficulty",
            "effort",
            "time",
            "bugs",
        )

    class Meta:
        """Define peewee meta data."""

        table_name = "radon_hal"
        indexes = ((("run", "dir", "filename"), True),)


class RadonHalFunction(BaseModel):
    """Radon "HAL" Function metric storage."""

    # fmt: off
    run               = ForeignKeyField(Run, backref="radon_hal_functions_run", on_delete="CASCADE")
    radon_hal_id      = ForeignKeyField(RadonHal, backref="radon_hal_functions", on_delete="CASCADE")

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
        indexes = ((("radon_hal_id", "name"), True),)


################################################################################################
# Queries..
################################################################################################
def query_raw(args: Namespace, level: str = "summary", run: Run = None, project: Project = None) -> Any:
    match level.lower():
        case "summary":
            return RadonRaw.select(
                fn.SUM(RadonRaw.loc).alias("loc"),
                fn.SUM(RadonRaw.lloc).alias("lloc"),
                fn.SUM(RadonRaw.sloc).alias("sloc"),
                fn.SUM(RadonRaw.comments).alias("comments"),
                fn.SUM(RadonRaw.multi).alias("multi"),
                fn.SUM(RadonRaw.blank).alias("blank"),
                fn.SUM(RadonRaw.single_comments).alias("single_comments"),
            ).where(RadonRaw.run == run.id)

        case "detail":
            rows = (
                RadonRaw.select(
                    RadonRaw.dir,
                    fn.SUM(RadonRaw.loc).alias("loc"),
                    fn.SUM(RadonRaw.lloc).alias("lloc"),
                    fn.SUM(RadonRaw.sloc).alias("sloc"),
                    fn.SUM(RadonRaw.comments).alias("comments"),
                    fn.SUM(RadonRaw.multi).alias("multi"),
                    fn.SUM(RadonRaw.blank).alias("blank"),
                    fn.SUM(RadonRaw.single_comments).alias("single_comments"),
                )
                .where(RadonRaw.run == run.id)
                .group_by(RadonRaw.dir)
                .order_by(RadonRaw.dir)
            )

            # Calculate totals
            totals = defaultdict(int)
            for row in rows:
                for attr in ("loc", "lloc", "sloc", "comments", "multi", "blank", "single_comments"):
                    totals[attr] += getattr(row, attr)
            return rows, totals

        case "full":
            return RadonRaw.select().where(RadonRaw.run == run.id).order_by(RadonRaw.dir, RadonRaw.filename)

        case _:
            raise RuntimeError(f"Sorry, invalid query level encountered! {level}")


def query_hal(args: Namespace, level: str = "summary", run: Run = None, project: Project = None) -> Any:
    match level.lower():
        case "summary":
            return (
                RadonHal.select(
                    RadonHal.dir,
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
                .group_by(RadonHal.dir)
                .where(RadonHal.run == run.id)
                .order_by(RadonHal.dir)
            )

        case "detail":
            rows = RadonHal.select().where(RadonHal.run == run.id).order_by(RadonHal.dir, RadonHal.filename)

            # Calculate means
            means = {}
            for attr in RadonHal.attributes():
                values = [getattr(row, attr) for row in rows]
                means[attr] = sum(values) / len(values) if values else None
            return rows, means

        case "full":
            rows = (
                RadonHalFunction.select(
                    RadonHal.dir,
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
                .where(RadonHal.run == run.id)
                .order_by(RadonHal.dir, RadonHal.filename, RadonHalFunction.name)
                .objects()
            )
            # Calculate mean metric values
            means = {}
            for attr in RadonHal.attributes():
                values = [getattr(row, attr) for row in rows]
                means[attr] = sum(values) / len(values) if values else None
            return rows, means

        case _:
            raise RuntimeError(f"Sorry, invalid query level encountered! {level}")


def query_mi(args: Namespace, level: str = "summary", run: Run = None, project: Project = None) -> Any:
    match level.lower():
        case "s" | "summary":
            return RadonMi.select(fn.AVG(RadonMi.mi).alias("mi_mean")).where(RadonMi.run == run.id).get()

        case "d" | "detail":
            rows = (
                RadonMi.select(RadonMi.dir, fn.AVG(RadonMi.mi).alias("mi_mean"))
                .where(RadonMi.run == run.id)
                .order_by(fn.AVG(RadonMi.mi).asc(), RadonMi.dir)
                .group_by(RadonMi.dir)
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

        case "f" | "full":
            rows = (
                RadonMi.select().where(RadonMi.run == run.id).order_by(RadonMi.mi.asc(), RadonMi.dir, RadonMi.filename)
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
            args_last = 2
            runs = (
                Run.select(Run.id)
                .where(
                    Run.project == project,
                    Run.module == MODULE,
                    Run.sub_module == "mi",
                )
                .order_by(Run.timestamp.desc())
                .limit(args_last)
            )
            run_ids = [run.id for run in runs]

            query = (
                RadonMi.select(
                    Run.timestamp.alias("timestamp"),
                    fn.AVG(RadonMi.mi).alias("mi_mean"),
                )
                .where(
                    RadonMi.run.in_(run_ids),
                )
                .join(Run)
                .group_by(Run.timestamp)
                .order_by(Run.timestamp.desc())
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
            roc = rate_of_change_percentage(transposed["mi"][timestamps[-2]], transposed["mi"][timestamps[-1]])

            return timestamps, transposed, roc

        case _:
            raise RuntimeError(f"Sorry, invalid query level encountered! {level}")


def query_cc(args: Namespace, level: str = "summary", run: Run = None, project: Project = None) -> Any:
    match level.lower():
        case "s" | "summary":
            return (
                RadonCc.select(
                    RadonCc.entity_type.alias("entity_type"),
                    fn.COUNT(RadonCc.id).alias("count"),
                )
                .where(RadonCc.run == run.id)
                .group_by(RadonCc.entity_type)
                .order_by(fn.COUNT(RadonCc.id).desc())
            )
            return RadonMi.select(fn.AVG(RadonMi.mi).alias("mi_mean")).where(RadonMi.run == run.id).get()

        case "d" | "detail":
            return (
                RadonCc.select(
                    RadonCc.dir,
                    RadonCc.entity_type,
                    fn.COUNT(RadonCc.id).alias("count"),
                )
                .where(RadonCc.run == run.id)
                .group_by(RadonCc.dir, RadonCc.entity_type)
                .order_by(RadonCc.dir, RadonCc.entity_type)
            )

        case "f" | "full":
            return (
                RadonCc.select(
                    RadonCc.dir,
                    RadonCc.filename,
                    RadonCc.entity_type,
                    fn.COUNT(RadonCc.id).alias("count"),
                )
                .where(RadonCc.run == run.id)
                .group_by(RadonCc.dir, RadonCc.filename, RadonCc.entity_type)
                .order_by(RadonCc.dir, RadonCc.filename, RadonCc.entity_type)
            )

        case _:
            raise RuntimeError(f"Sorry, invalid query level encountered! {level}")
