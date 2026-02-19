"""Setup applications logging configuration."""

import logging
from argparse import Namespace

from rich.console import Console
from rich.logging import RichHandler


################################################################################################
def setup_logging(args: Namespace, arg_peewee_debug: bool = False) -> logging.Logger:
    level = getattr(logging, args.log_level.upper())
    peewee_level = "DEBUG" if arg_peewee_debug else "INFO"

    # def emit(self, record):
    #     """Override emit to modify the record before rendering"""
    #     # Customize what shows on the right side
    #     parts = record.name.split(".")
    #     short_name = ".".join(parts[-2:]) if len(parts) >= 2 else record.name

    #     # RichHandler uses record.pathname for the path display
    #     # We'll fake it to show our custom format
    #     record.pathname = short_name
    #     record.filename = short_name

    #     super().emit(record)

    # # Custom formatter that shows parent.module
    # class ShortModuleFormatter(logging.Formatter):
    #     def format(self, record):
    #         parts = record.name.split(".")
    #         record.short_name = ".".join(parts[-2:]) if len(parts) >= 2 else record.name
    #         return super().format(record)

    # Setup Rich handler
    rich_handler = CustomRichHandler(
        console=Console(),
        show_time=True,
        show_path=True,
        rich_tracebacks=True,
        tracebacks_show_locals=False,
    )

    # Setup the formatter using our custom one above.
    # formatter = ShortModuleFormatter(fmt="[%(short_name)s:%(lineno)d] %(message)s", datefmt="[%X]")
    # rich_handler.setFormatter(formatter)
    rich_handler.setFormatter(logging.Formatter(fmt="%(message)s", datefmt="[%X]"))

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()  # Remove any existing handlers
    root_logger.setLevel(level)
    root_logger.addHandler(rich_handler)

    # Configure uvicorn logger specifically
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.handlers.clear()  # Remove uvicorn's default handlers
    uvicorn_logger.addHandler(rich_handler)  # Replace with our nicer handler..
    uvicorn_logger.setLevel(level)
    uvicorn_logger.propagate = False  # Don't propagate to root to avoid duplicates

    # Also configure uvicorn.access if you want access logs formatted too
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.handlers.clear()
    access_logger.addHandler(rich_handler)
    access_logger.propagate = False

    # Configure Peewee logger explicitly
    peewee_logger = logging.getLogger("peewee")
    peewee_logger.handlers.clear()
    peewee_logger.addHandler(rich_handler)
    peewee_logger.setLevel(peewee_level)  # Allows us to segregate sql logging if desired.
    peewee_logger.propagate = False

    # Turn off asyncio logging
    asyncio_logger = logging.getLogger("asyncio")
    asyncio_logger.setLevel(logging.WARNING)


class CustomRichHandler(RichHandler):
    """RichHandler that shows parent.module:lineno on the right."""

    def emit(self, record):
        """Override emit to modify the record before rendering."""
        # Customize what shows on the right side
        parts = record.name.split(".")
        short_name = ".".join(parts[-2:]) if len(parts) >= 2 else record.name

        # RichHandler uses record.pathname for the path display
        # We'll fake it to show our custom format
        record.pathname = short_name
        record.filename = short_name

        super().emit(record)
