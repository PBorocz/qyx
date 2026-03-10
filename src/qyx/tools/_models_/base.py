"""Define all the "core" peewee models, ie. over and above "tool"-specific storage."""

import peewee as pw


################################################################################################
# Base Peewee Model Definitions (ie. database tables)
################################################################################################
class BaseModel(pw.Model):
    """Root model of all Peewee models."""

    class Meta:
        """Define peewee orm/table semantics."""

        database = None
