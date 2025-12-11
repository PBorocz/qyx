"""..."""

import os

from peewee import CharField, IntegerField

from mq.models import BaseModuleModel


class Ruff(BaseModuleModel):
    """..."""

    # fmt: off
    line      = IntegerField(null=False)
    column    = IntegerField(null=False)
    rule_code = CharField(help_text="Eg. E302, PLC123 etc.",null=False)
    message   = CharField(null=False)
    # fmt: on

    class Meta:
        """..."""

        table_name = "ruff"
        indexes = (("run_id", "dir", "filename", "line", "column", "rule_code"), True)
