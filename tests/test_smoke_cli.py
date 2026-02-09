"""Run all the reports across all tool/analyses and levels."""

from argparse import Namespace

import pytest

from mq.cli.status import status
from mq.constants import StatusLevel
from mq.setup.args_configuration import setup_configuration
from mq.setup.logging import setup_logging
from mq.setup.sqlite import setup_sqlite
from mq.setup.tools import setup_tools
from mq.tools.base import Project


@pytest.fixture(scope="session")
def test_args():
    """Setup our application (mostly database connection and registration)."""
    args = Namespace(log_level="warning")
    _, _, args.config = setup_configuration()
    setup_logging(args)
    setup_tools(args)
    setup_sqlite(args)
    yield args


def test_status(test_args, subtests, capsys):
    cases = []
    for project in Project.select():
        for level in StatusLevel:
            cases.append((project.name, level))

    for project_name, level in cases:
        with subtests.test(project=project_name, level=level):
            test_args.name, test_args.level = project_name, level

            # Run the test...
            status(test_args)

            # If we got here, no exceptions where raised.
            # Did the output at least have the project information?
            captured = capsys.readouterr()
            assert "PROJECT" in captured.out
            assert project_name in captured.out


def test_cli_rendering_methods(test_args, subtests, capsys):
    cases = []
    for o_tool in test_args.tools.values():
        render_method = o_tool.render_cli_method
        for analysis, report_level in o_tool.iter_reports("cli"):
            for project in Project.select():
                message = f"{o_tool.name}:{analysis}:{report_level.value} - ID:{project.id}"
                case = Namespace(
                    message=message,
                    o_tool=o_tool,
                    render_method=render_method,
                    analysis=analysis,
                    level=report_level,
                    project=project,
                )
                cases.append(case)

    for case in cases:
        with subtests.test(message=case.message, case=case):
            test_args.name, test_args.level = case.project.name, case.level

            # Run the test...
            case.render_method(test_args, case.project, case.o_tool, case.analysis)

            # If we got here, no exceptions where raised.
            # Did the output at least have the project information?
            captured = capsys.readouterr()
            if case.o_tool.name.upper() not in captured.out:
                breakpoint()

            assert case.o_tool.name.upper() in captured.out
