"""Run all the reports across all tool/analyses and levels."""

import tempfile
from pathlib import Path
from argparse import Namespace

import pytest

from mq.cli.ingest import ingest
from mq.setup.args_configuration import setup_configuration
from mq.setup.logging import setup_logging
from mq.setup.sqlite import setup_sqlite
from mq.setup.tools import setup_tools
from mq.tools.base import Project, Request, Scan

TEST_PROJECT = "__test_project__"


@pytest.fixture(scope="session")
def db_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test.db"


@pytest.fixture(scope="session")
def app_args(db_path):
    """Setup our application (mostly database connection and registration)."""
    args = Namespace(
        log_level="warning",
        db_path=db_path,
        tool_analysis=None,  # Will force us to ingest all tools & analyses
        stdin=None,  # Will force us to use respective tools to ingest
        path=str(Path(__file__).parent.parent),  # str as if we're getting from the command-line
        name=TEST_PROJECT,
    )
    _, _, args.config = setup_configuration()
    setup_logging(args)
    setup_tools(args)
    setup_sqlite(args)
    yield args


@pytest.fixture(scope="session")
def ingested_project(app_args):
    """Ingest our own project for testing, return our project instance."""
    ingest(app_args)

    # Confirm we get setup correctly!
    assert Project.select().count() == 1, "Sorry, we should have a project instance in our test db!"
    assert Request.select().count() == 1, "Sorry, we should have a matching request instance in our test db!"
    assert Scan.select().count() > 0, "Sorry, we should have at least 1 scan instance in our test db!"
    try:
        ingested_project = Project.get(Project.name == TEST_PROJECT)
    except Project.DoesNotExist:
        pytest.fail(f"Sorry, unable to find project with name:{TEST_PROJECT} in our test db!")
    yield ingested_project
