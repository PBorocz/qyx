"""..."""

from peewee import CharField, DateTimeField, Model


class Run(Model):
    """..."""

    # fmt: off
    ################################################################################
    # Required (remember that "id" attribute will be automatically added by peewee)
    ################################################################################
    timestamp       = DateTimeField(help_text="GMT/UTC datetime the ingest occurred")
    git_commit_hash = CharField    (help_text="ID from respective sport's site")
    source_dir      = CharField    (help_text="Pointer to respective sport's id attribute, e.g. 'cycling'")
    run_module      = CharField    (help_text="Match SchedulesDirect, usually '<yyyymmdd>.<awayTeam>@<homeTeam>'")
    # fmt: on
