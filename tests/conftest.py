"""Setup the database, args and an ingested project."""

import tempfile
from argparse import Namespace
from pathlib import Path

import pytest

from qyx.constants import ALL_ITEMS
from qyx.cli.ingest import ingest
from qyx.setup.args_configuration import setup_configuration
from qyx.setup.logging import setup_logging
from qyx.setup.sqlite import setup_sqlite
from qyx.setup.tools import setup_tools
from qyx.tools._models_ import Project, Request, Scan

TEST_PROJECT = "__test_project__"


@pytest.fixture(scope="session")
def db_path(memory=False):
    if memory:
        return ":memory:"
    with tempfile.TemporaryDirectory() as tmpdir:
        return Path(tmpdir) / "test.db"


@pytest.fixture(scope="session")
def app_args(db_path):
    """Setup our application (mostly database connection and registration)."""
    args = Namespace(
        log_level="warning",
        db_path=db_path,
        stdin=None,  # Will force us to use respective tools to ingest
        path=str(Path(__file__).parent.parent),  # str as if we're getting from the command-line
        name=TEST_PROJECT,
        tool=ALL_ITEMS,
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
