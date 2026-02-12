"""..."""

from argparse import Namespace

import pytest

from qyx.tools.base import Scan


def _get_test_cases(app_args, ingested_project):
    cases = []
    for o_tool in app_args.tools.values():
        for analysis, report_level in o_tool.iter_reports("web"):
            tool = o_tool.name

            scan = Scan.get_most_recent(ingested_project, tool, analysis)

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
            msg = f"T:{o_tool.name} A:{analysis} L:{report_level.value}]"
            cases.append(Namespace(msg=msg, scan=scan, web_render_method=web_render_method))
    return cases


def test_web_rendering_methods(app_args, ingested_project, subtests):
    """Test that each URL returns a valid HTTP status code."""
    for case in _get_test_cases(app_args, ingested_project):
        with subtests.test(case.msg):
            #
            # Run the test (running without error is our primary test!!)
            #
            result = case.web_render_method(
                app_args,
                project=ingested_project,
                scan=case.scan,
            )

            # Check if we got back any of the valid possibilities:
            # - None (is ok as some projects may not have scan or the scans have no results)
            # - HTML (on behalf of plotly methods)
            # - FastHTML components.
            match result:
                case None:
                    pass
                case bytes() as html:
                    assert html.startswith(b"<html>")
                    assert html.endswith(b"</html>")
                case dict():
                    for html in result.values():
                        assert html.startswith(b"<html>")
                        assert html.endswith(b"</html>")
                case tuple() as components if len(components) > 0:
                    for component in components:
                        assert hasattr(component, "__ft__") or hasattr(component, "to_xml")
                case tuple():  # Empty tuple
                    pass
                case _:
                    breakpoint()
                    pytest.fail(f"Unexpected return type: {type(result)}")
