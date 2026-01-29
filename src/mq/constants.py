"""Constants and types."""

from enum import Enum


class ConfigurationError(ValueError):
    """Raised when there's an error in configuration, specifically tool setup."""

    pass


class BaseModel(str, Enum):
    """Base data models."""

    # fmt: off
    SCAN    = "scan"
    REQUEST = "request"
    PROJECT = "project"
    # fmt: on


class StatusLevel(str, Enum):
    """Levels available for status command."""

    # fmt: off
    GROUPED    = "g"
    INDIVIDUAL = "i"
    # fmt: on

    @property
    def description(self):
        """More granular definitions."""
        descriptions = {
            "g": "Grouped Scans",
            "i": "Individual Scans (might be a lot!)",
        }
        return descriptions[self.value]


class ReportLevel(str, Enum):
    """Levels available for report command."""

    # fmt: off
    SUMMARY   = "0"
    DIRECTORY = "1"
    FILE      = "2"
    DETAIL    = "3"
    DERIVED   = "d"
    HISTORY   = "h"
    # fmt: on

    @property
    def description(self):
        """More granular definitions."""
        descriptions = {
            "0": "Summary",
            "1": "Directory",
            "2": "File",
            "3": "Deep!",
            "d": "Derived",
            "h": "History",
        }
        return descriptions[self.value]


class LogLevel(str, Enum):
    """Logging levels available for all commands."""

    # fmt: off
    INFO     = "info"
    DEBUG    = "debug"
    WARNING  = "warning"
    ERROR    = "error"
    CRITICAL = "critical"
    # fmt: on
