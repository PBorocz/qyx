"""Constants and types."""

from enum import Enum


class ConfigurationError(ValueError):
    """Raised when there's an error in configuration, specifically tool setup."""

    pass


class BaseModel(str, Enum):
    """Base (non-application internal) data models."""

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
        return descriptions.get(self.value, "-")


class ReportLevel(str, Enum):
    """Levels available for report command."""

    # Note: we tie the "values" of this enum to actual method calls
    # so be very careful renaming! for example: tools/radon/cli.py:20

    # fmt: off
    SUMMARY   = "0"
    DIRECTORY = "1"
    FILE      = "2"
    GRANULAR  = "3"  # Primarily used for Radon @class/method/function level; other tools: TBD
    DERIVED   = "d"
    HISTORY   = "h"
    ALL       = "*"
    # fmt: on

    @property
    def description(self):
        """More granular definitions."""
        descriptions = {
            "0": "Summary",
            "1": "Directory",
            "2": "File",
            "3": "Granular",
            "d": "Derived",
            "h": "History",
            "*": "-All-",
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
