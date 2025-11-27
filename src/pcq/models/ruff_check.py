"""..."""

from peewee import CharField, IntegerField, ForeignKeyField, Model

from pcq.models import Run


class RuffCheck(Model):
    """..."""

    # fmt: off
    ################################################################################
    # Required (remember that "id" attribute will be automatically added by peewee)
    ################################################################################
    run_id    = ForeignKeyField (Run, backref="Ruff checks")
    filename  = CharField       (help_text="")
    line      = IntegerField    ()
    column    = IntegerField    ()
    rule_code = CharField       (help_text="")
    message   = CharField       (help_text="")
    severity  = CharField       (help_text="")
    # fmt: on
