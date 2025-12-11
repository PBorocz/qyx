"""..."""

from peewee import CharField, IntegerField, ForeignKeyField, Model

from mq.models import Run


class Cloc(Model):
    """..."""

    # fmt: off
    ################################################################################
    # Required (remember that "id" attribute will be automatically added by peewee)
    ################################################################################
    run_id        = ForeignKeyField(Run, backref="Cloc")
    dir           = CharField()
    filename      = CharField()
    lines_blank   = IntegerField()
    lines_code    = IntegerField()
    lines_comment = IntegerField()
    scale_factor  = IntegerField()
    # fmt: on

    class Meta:
        """..."""

        table_name = "cloc"
