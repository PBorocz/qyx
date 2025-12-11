"""..."""

import os

from peewee import CharField, IntegerField

from mq.modules.models import BaseModuleModel


class Ruff(BaseModuleModel):
    """..."""

    # fmt: off
    line      = IntegerField()
    column    = IntegerField()
    rule_code = CharField(help_text="Eg. E302, PLC123 etc.")
    message   = CharField()
    url       = CharField(null=True)
    # fmt: on

    class Meta:
        """..."""

        table_name = "ruff"
        indexes = ((("run_id", "dir", "filename", "line", "column", "rule_code"), True),)
