"""..."""

from peewee import CharField, FloatField, IntegerField, ForeignKeyField

from mq.models import BaseModuleModel


class RadonRaw(BaseModuleModel):
    """Radon "RAW" metric storage."""

    # fmt: off
    loc             = IntegerField(null=False, help_text="Lines of code")
    lloc            = IntegerField(null=False, help_text="Logical lines of code")
    sloc            = IntegerField(null=False, help_text="Source lines of code")
    comments        = IntegerField(null=False, help_text="Comment lines")
    multi           = IntegerField(null=False, help_text="Multi-line strings")
    blank           = IntegerField(null=False, help_text="Blank lines")
    single_comments = IntegerField(null=False, help_text="Single-line comments")
    # fmt: on

    class Meta:
        """Define peewee meta data."""

        table_name = "radon_raw"
        indexes = (("run_id", "dir", "filename"), True)


class RadonMi(BaseModuleModel):
    """Radon "MI" metric storage."""

    # fmt: off
    mi   = FloatField(null=False, help_text="Maintainability index")
    rank = CharField(null=False, help_text="Grade, ie. A, B, C, etc.")
    # fmt: on

    class Meta:
        """Define peewee meta data."""

        table_name = "radon_mi"
        indexes = (("run_id", "dir", "filename"), True)


class RadonCc(BaseModuleModel):
    """Radon "CC" metric storage."""

    # fmt: off
    entity_type   = CharField(help_text="F, M or C (function, method or class)", null=False)
    entity_name   = CharField(help_text="main, <class>.method, etc.", null=False)
    line_start    = IntegerField(null=False)
    line_end      = IntegerField(null=False)
    column_offset = IntegerField(null=False)
    rank          = CharField(help_text="Complexity grade, ie. A, B, C...", null=False)
    complexity    = IntegerField(help_text="Raw complexity score", null=False)
    # fmt: on

    class Meta:
        """Define peewee meta data."""

        table_name = "radon_cc"
        indexes = (("run_id", "dir", "filename", "entity_type", "entity_name"), True)


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

    class Meta:
        """Define peewee meta data."""

        table_name = "radon_hal"
        indexes = (("run_id", "dir", "filename"), True)


class RadonHalFunction(BaseModuleModel):
    """Radon "HAL" Function metric storage."""

    # fmt: off
    radon_hal_id      = ForeignKeyField(RadonHal, backref="Radon Maintainability checks", null=False)

    name              = CharField(help_text="function name", null=False)
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
        indexes = (("radon_hal_id", "name"), True)
