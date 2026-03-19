"""..."""

import inspect

from types import SimpleNamespace as Sns

from qyx.constants import ReportLevel
from qyx.tools._models_ import Scan


def _get_granular_view_cases(app_args, ingested_project):
    cases = []
    for o_tool in app_args.tools.tools():
        for report_level in ReportLevel:
            for o_dimension in o_tool.dimensions:
                tool, dimension = o_tool.name, o_dimension.name

                scan = Scan.get_latest(ingested_project, tool, dimension)

                # Lookup the correct web rendering method. Note, this could from *either*:
                # - <tool>/web.py             (eg. ruff, cloc etc.)
                # - <tool>/web_<dimension>.py (eg. radon with it's sub-analyses)
                try:
                    render_method_name = f"view_{dimension}_{report_level.value}"
                    web_view_module = o_tool.import_component("web")
                    web_view_method = getattr(web_view_module, render_method_name)
                except (ModuleNotFoundError, AttributeError):
                    try:
                        web_view_module = o_tool.import_component(f"web_{dimension}")
                        web_view_method = getattr(web_view_module, render_method_name)
                    except (ModuleNotFoundError, AttributeError):
                        continue
                        # pytest.fail(
                        #     f"Missing web view method '{render_method_name}' for tool={tool}, dimension={dimension}",
                        #     pytrace=False,  # optional: cleaner output without pytest internals
                        # )

                msg = f"T:{o_tool.name} D:{dimension} L:{report_level.value}]"
                cases.append(Sns(msg=msg, scan=scan, web_view_method=web_view_method))
    return cases


def call_test_with_args(func, **kwargs):
    """Call func with only the arguments it accepts from kwargs (thanks Claude ;-)."""
    sig = inspect.signature(func)
    valid_params = sig.parameters.keys()
    filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_params}
    return func(**filtered_kwargs)


def test_web_views(app_args, ingested_project, subtests):
    """Test that each URL returns a valid HTTP status code."""
    for case in _get_granular_view_cases(app_args, ingested_project):
        with subtests.test(case.msg):
            #
            # Run the test (running without error is our primary test!!)
            #
            result = call_test_with_args(
                case.web_view_method,
                args=app_args,
                project=ingested_project,
                scan=case.scan,
            )

            # Check if we got back any of the valid possibilities:
            # - None (is ok as some projects may not have scan or the scans have no results)
            # - HTML
            match result:
                case None:
                    pass

                case Sns():
                    pass  # Expected output!

                case dict():
                    pass

                case list():
                    # Only happens when return raw Sns's
                    for foo in result:
                        assert isinstance(foo, Sns)

                case str() as html:
                    assert html.startswith("<html>")
                    assert html.endswith("</html>")

                case _:
                    if not hasattr(result, "__data__"):
                        print(f"Unexpected return type: {type(result)}")
                        breakpoint()
                        # pytest.fail(f"Unexpected return type: {type(result)}")
