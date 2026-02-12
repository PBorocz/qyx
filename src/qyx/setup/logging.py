"""Setup applications logging configuration."""

import logging
from argparse import Namespace

from rich.console import Console
from rich.logging import RichHandler


################################################################################################
def setup_logging(args: Namespace, arg_peewee_debug: bool = False) -> logging.Logger:
    level = getattr(logging, args.log_level.upper())
    peewee_level = "DEBUG" if arg_peewee_debug else "INFO"

    # Setup Rich handler
    rich_handler = RichHandler(
        console=Console(),
        show_time=True,
        show_path=True,
        rich_tracebacks=True,
        tracebacks_show_locals=False,
    )
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
