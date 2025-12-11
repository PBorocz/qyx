"""..."""

from peewee import IntegerField

from mq.models import BaseModuleModel


class Cloc(BaseModuleModel):
    """..."""

    # fmt: off
    lines_blank   = IntegerField(null=False)
    lines_code    = IntegerField(null=False)
    lines_comment = IntegerField(null=False)
    scale_factor  = IntegerField(null=False)
    # fmt: on

    class Meta:
        """Define peewee meta data."""

        table_name = "cloc"
        indexes = (("run_id", "dir", "filename"), True)
