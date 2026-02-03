"""..."""

from argparse import Namespace

import pytest

from mq.tools.base import Project, Scan
from mq.setup.args_configuration import setup_configuration
from mq.setup.logging import setup_logging
from mq.setup.sqlite import setup_sqlite
from mq.setup.tools import setup_tools


@pytest.fixture(scope="session")
def test_args():
    """Setup our application (mostly database connection and registration)."""
    args = Namespace(log_level="warning")
    _, _, args.config = setup_configuration()
    setup_logging(args.log_level)
    setup_tools(args)
    setup_sqlite(args)
    yield args


def _get_test_cases(test_args):
    cases = []
    for o_tool in test_args.tools.values():
        for analysis, report_level in o_tool.iter_reports("web"):
            for project in Project.select():
                tool = o_tool.name
                description = f"T:{tool} A:{analysis} L:{report_level.value} P:{project.name} [{project.id}]"

                scan = Scan.get_most_recent(project, tool, analysis)

                # Lookup the correct web rendering method. Note, this could from either:
                # - <tool>/web.py            (e.g. ruff, cloc etc.)
                # - <tool>/web_<analysis>.py (e.g. radon with it's sub-analyses)
                render_method_name = f"{analysis}_{report_level.value}"
                try:
                    web_render_module = o_tool.import_component("web")
                    web_render_method = getattr(web_render_module, render_method_name)
                except AttributeError:
                    try:
                        web_render_module = o_tool.import_component(f"web_{analysis}")
                        web_render_method = getattr(web_render_module, render_method_name)
                    except AttributeError:
                        raise RuntimeError(
                            f"Sorry, unable to setup test case: {tool} {render_method_name}",
                        )
                case = Namespace(
                    description=description,
                    project=project,
                    scan=scan,
                    web_render_method=web_render_method,
                )
                cases.append(case)
    return cases


def test_web_rendering_methods(test_args, subtests):
    """Test that each URL returns a valid HTTP status code."""
    for case in _get_test_cases(test_args):
        with subtests.test(case.description):
            # Run the test (running without error is our primary test!!)
            result = case.web_render_method(test_args, project=case.project, scan=case.scan)

            # Check if we got back any of the valid possibilities:
            # - None (is ok as some projects may not have scan or the scans have no results)
            # - SVG
            # - FastHTML components.
            match result:
                case None:
                    pass
                case bytes() as svg:
                    assert svg.startswith(b"<svg") or svg.startswith(b"<?xml")
                    assert b"</svg>" in svg
                case dict():
                    for svg in result.values():
                        assert svg.startswith(b"<svg") or svg.startswith(b"<?xml")
                        assert b"</svg>" in svg
                case tuple() as components if len(components) > 0:
                    for component in components:
                        assert hasattr(component, "__ft__") or hasattr(component, "to_xml")
                case tuple():  # Empty tuple
                    pass
                case _:
                    breakpoint()
                    pytest.fail(f"Unexpected return type: {type(result)}")
