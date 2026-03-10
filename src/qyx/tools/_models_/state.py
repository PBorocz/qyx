"""Define all the "core" peewee models, ie. over and above "tool"-specific storage."""

from __future__ import annotations

import logging
from argparse import Namespace
from datetime import datetime, UTC

import peewee as pw

from .base import BaseModel


log = logging.getLogger(__name__)


class State(BaseModel):
    """Key-value store for application state."""

    key = pw.CharField(primary_key=True, max_length=100)
    value = pw.TextField()
    updated = pw.DateTimeField(default=lambda: datetime.now(UTC).replace(microsecond=0))

    @classmethod
    def update(cls, args: Namespace, **kwargs):
        """Update state fields atomically."""
        with args._db.atomic():
            for key, value in kwargs.items():
                if value is None:
                    # Delete the key if value is None
                    State.delete().where(State.key == key).execute()
                else:
                    # Otherwise, simply replace it.
                    State.replace(key=key, value=str(value)).execute()
                log.debug(f"state: {key=} -> {value=}")

    @classmethod
    def lookup(cls, key: str, default=None):
        """Get a single state value."""
        try:
            return State.get(State.key == key.lower()).value
        except State.DoesNotExist:
            return default
