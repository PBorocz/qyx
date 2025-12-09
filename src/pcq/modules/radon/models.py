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


def remove_common_prefixes(rows: list) -> list:
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
