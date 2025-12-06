"""..."""

import os

from peewee import CharField, IntegerField, ForeignKeyField, Model

from pcq.models import Run


class RuffCheck(Model):
    """..."""

    # fmt: off
    ################################################################################
    # Required (remember that "id" attribute will be automatically added by peewee)
    ################################################################################
    run_id    = ForeignKeyField(Run, backref="Ruff checks")
    filename  = CharField      (help_text="")
    line      = IntegerField   ()
    column    = IntegerField   ()
    rule_code = CharField      (help_text="")
    message   = CharField      (help_text="")
    # fmt: on

    class Meta:
        """..."""

        table_name = "ruff_check"


def remove_common_prefixes(rows: list[RuffCheck]) -> list[RuffCheck]:
    """Remove common prefix from a list of file paths."""
    if not rows:
        return []

    paths = [row.filename for row in rows]
    if not paths:
        return []

    # Find the common prefix
    common_prefix = os.path.commonpath(paths)

    for row in rows:
        row.filename = os.path.relpath(row.filename, common_prefix)
    return rows
