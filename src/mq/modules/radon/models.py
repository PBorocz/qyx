"""..."""

from peewee import CharField, FloatField, IntegerField, ForeignKeyField

from mq.modules.models import BaseModel, BaseModuleModel, Run


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
        indexes = ((("run_id", "dir", "filename"), True),)


class RadonMi(BaseModuleModel):
    """Radon "MI" metric storage."""

    # fmt: off
    mi   = FloatField(help_text="Maintainability index")
    rank = CharField(help_text="Grade, ie. A, B, C, etc.")
    # fmt: on

    class Meta:
        """Define peewee meta data."""

        table_name = "radon_mi"
        indexes = ((("run_id", "dir", "filename"), True),)


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
        indexes = ((("run_id", "dir", "filename", "entity_type", "entity_name"), True),)


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
        indexes = ((("run_id", "dir", "filename"), True),)


class RadonHalFunction(BaseModel):
    """Radon "HAL" Function metric storage."""

    # fmt: off
    run_id            = ForeignKeyField(Run, backref="run")
    radon_hal_id      = ForeignKeyField(RadonHal, backref="radon_hal")

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
