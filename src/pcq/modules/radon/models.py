"""..."""

import os

from peewee import CharField, FloatField, IntegerField, ForeignKeyField, Model

from pcq.models import Run


class RadonRaw(Model):
    """..."""

    # fmt: off
    run_id          = ForeignKeyField(Run, backref="Radon Raw checks")
    dir             = CharField()
    filename        = CharField()
    loc             = IntegerField()
    lloc            = IntegerField()
    sloc            = IntegerField()
    comments        = IntegerField()
    multi           = IntegerField()
    blank           = IntegerField()
    single_comments = IntegerField()
    # fmt: on

    class Meta:
        """..."""

        table_name = "radon_raw"


class RadonMi(Model):
    """..."""

    # fmt: off
    run_id   = ForeignKeyField(Run, backref="Radon Maintainability checks")
    dir      = CharField()
    filename = CharField()
    mi       = FloatField()
    rank     = CharField()
    # fmt: on

    class Meta:
        """..."""

        table_name = "radon_mi"


class RadonCc(Model):
    """..."""

    # fmt: off
    run_id        = ForeignKeyField(Run, backref="Radon Maintainability checks")
    dir           = CharField()
    filename      = CharField()
    entity_type   = CharField(help_text="F, M or C (function, method or class)")
    entity_name   = CharField(help_text="main, <class>.method, etc.")
    line_start    = IntegerField()
    line_end      = IntegerField()
    column_offset = IntegerField()
    rank          = CharField(help_text="Complexity grade, ie. A, B, C...")
    complexity    = IntegerField(help_text="Raw complexity score")
    # fmt: on

    class Meta:
        """..."""

        table_name = "radon_cc"


class RadonHal(Model):
    """..."""

    # fmt: off
    run_id            = ForeignKeyField(Run, backref="Radon Maintainability checks")
    dir               = CharField()
    filename          = CharField()

    h1		      = IntegerField(help_text="total distinct operators")
    h2		      = IntegerField(help_text="total distinct operands")
    N1		      = IntegerField(help_text="total operators in file")
    N2		      = IntegerField(help_text="total operands in file")
    program_vocabulary= IntegerField(help_text="total vocabulary (h = h1 + h2)")
    program_length    = IntegerField(help_text="total length (N = N1 + N2)")
    calculated_length = IntegerField(help_text="(see wikipedia page!)")
    volume            = FloatField(help_text="total volume (V = N log2 h)")
    difficulty        = FloatField(help_text="average difficulty across functions (D = ((h1/2) * (N2/h2)))")
    effort            = FloatField(help_text="total effort (E = D * V)")
    time              = FloatField(help_text="total time (T = (E / 18) in seconds)")
    bugs              = FloatField(help_text="estimated bugs for file (B = V / 3000)")
    # fmt:

    class Meta:
        """..."""

        table_name = "radon_hal"


class RadonHalFunction(Model):
    """..."""

    # fmt: off
    run_id            = ForeignKeyField(Run, backref="Radon Run")
    radon_hal_id      = ForeignKeyField(RadonHal, backref="Radon Maintainability checks")
    name              = CharField(help_text="function name")

    h1		      = IntegerField(help_text="total distinct operators")
    h2		      = IntegerField(help_text="total distinct operands")
    N1		      = IntegerField(help_text="total operators in file")
    N2		      = IntegerField(help_text="total operands in file")
    program_vocabulary= IntegerField(help_text="total vocabulary (h = h1 + h2)")
    program_length    = IntegerField(help_text="total length (N = N1 + N2)")
    calculated_length = IntegerField(help_text="(see wikipedia page!)")
    volume            = FloatField(help_text="total volume (V = N log2 h)")
    difficulty        = FloatField(help_text="average difficulty across functions (D = ((h1/2) * (N2/h2)))")
    effort            = FloatField(help_text="total effort (E = D * V)")
    time              = FloatField(help_text="total time (T = (E / 18) in seconds)")
    bugs              = FloatField(help_text="estimated bugs for file (B = V / 3000)")
    # fmt:

    class Meta:
        """..."""

        table_name = "radon_hal_function"
