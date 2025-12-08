"""..."""

from peewee import CharField, IntegerField, ForeignKeyField, Model

from pcq.models import Run


class Cloc(Model):
    """..."""

    # fmt: off
    ################################################################################
    # Required (remember that "id" attribute will be automatically added by peewee)
    ################################################################################
    run_id        = ForeignKeyField(Run, backref="Cloc")
    dir           = CharField      (help_text="Directory under root")
    file_name     = CharField      (help_text="Filename within dir")
    lines_blank   = IntegerField   (help_text="Number of blank lines")
    lines_code    = IntegerField   (help_text="Number of code lines")
    lines_comment = IntegerField   (help_text="Number of comment lines")
    scale_factor  = IntegerField   (help_text="cloc scale factor")
    # fmt: on

    class Meta:
        """..."""

        table_name = "cloc"
