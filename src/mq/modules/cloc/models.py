"""..."""

from peewee import IntegerField

from mq.modules.models import BaseModuleModel


class Cloc(BaseModuleModel):
    """..."""

    # fmt: off
    lines_blank   = IntegerField(null=True)
    lines_code    = IntegerField(null=True)
    lines_comment = IntegerField(null=True)
    scale_factor  = IntegerField(null=True)
    # fmt: on

    class Meta:
        """Define peewee meta data."""

        table_name = "cloc"
        indexes = ((("run_id", "dir", "filename"), True),)
