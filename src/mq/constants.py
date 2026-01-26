"""Constants and types."""

from enum import Enum


class ReportLevel(str, Enum):
    """Levels available for report command."""

    # fmt: off
    SUMMARY   = "0"
    DIRECTORY = "1"
    FILE      = "2"
    DETAIL    = "3"
    DIFF      = "d"
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
