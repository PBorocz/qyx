"""Define all the "core" peewee models, ie. over and above "tool"-specific storage."""

from dataclasses import dataclass
from typing import Literal

import peewee as pw


################################################################################################
# Base Peewee Model Definitions (ie. database tables)
################################################################################################
class BaseModel(pw.Model):
    """Root model of all Peewee models."""

    class Meta:
        """Define peewee orm/table semantics."""

        database = None


################################################################################################
# supporting...
################################################################################################
@dataclass(frozen=True)
class ModelAttribute:
    """Represents a model attribute/metric with its metadata."""

    display: str
    calculation: str
    name: str
    type: Literal["float", "int", "str"]
