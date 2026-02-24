"""Run all the reports across all tool/analyses and levels."""

from argparse import Namespace

import pytest

from qyx.cli.status import status
from conftest import TEST_PROJECT


def test_status(app_args, ingested_project, capsys):
    """Test status command output."""
    status(app_args)

    # Did the output at least have the project information?
    captured = capsys.readouterr()
    assert "PROJECT" in captured.out
    assert "REQUEST" in captured.out
    assert "SCAN" in captured.out
    assert TEST_PROJECT in captured.out


def test_cli_rendering_methods(app_args, ingested_project, subtests, capsys):
    """Test all tool CLI rendering methods across analyses and levels."""
    cases = []
    for o_tool in app_args.tools.values():
        for analysis, report_level in o_tool.iter_reports("cli"):
            msg = f"T:{o_tool.name} A:{analysis} L:{report_level.value}]"
            cases.append(Namespace(msg=msg, o_tool=o_tool, analysis=analysis, level=report_level))

    for case in cases:
        with subtests.test(case.msg):
            app_args.name = ingested_project.name
            app_args.level = case.level

            # Run the test...
            case.o_tool.render_cli_method(
                app_args,
                ingested_project,
                case.o_tool,
                case.analysis,
            )

            # If we got here, no exceptions where raised.
            # Did the output at least have the project information?
            captured = capsys.readouterr()
            if case.o_tool.name.upper() not in captured.out:
                print(captured.out)
                pytest.fail(f"Sorry, unable to find {case.o_tool.name.upper()=} in status output!")
