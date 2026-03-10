"""..."""

import socket
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

import pytest

from qyx.tools._models_ import Project
from qyx.web.serve import create_app


def is_port_in_use(port: int) -> bool:
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def wait_for_server(url: str, timeout: int = 10) -> bool:
    """Wait for server to be ready."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with urlopen(url, timeout=1):
                return True
        except (HTTPError, URLError):
            # Server responded (even with error), so it's up
            return True
        except Exception:
            time.sleep(0.25)
    return False


@pytest.fixture(scope="session")
def server_and_args(app_args, ingested_project):
    # Base URL for your local web service
    port = 5012
    base_url = f"http://localhost:{port}"

    """Start the web server before tests and stop it after."""
    # Check if server is already running
    if is_port_in_use(port):
        pytest.skip(f"Port {port} is already in use. Using existing server.")
        yield
        return

    # Override whatever's the current defaults are
    app_args.browser = False
    app_args.port = port

    # Create the (Bottle) app
    app = create_app(app_args)

    # ...and run it a background thread (thanks Claude!)
    thread = threading.Thread(
        target=run_bottle,
        args=(app, port),
        daemon=True,
    )
    thread.start()

    health_url = f"{base_url}/health"
    if not wait_for_server(health_url, timeout=20):
        pytest.fail("Server failed to start within timeout")
    print(f"\n↑ Test server successfully started ({port=})")

    time.sleep(1)
    yield (app, app_args)

    # Cleanup: Bottle doesn't have a clean shutdown mechanism when run in thread
    # The daemon thread will be killed when tests exit
    print(f"\n↓ Test server shut down ({port=})")


def run_bottle(app, port):
    """Setup Bottle server in a background thread."""
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        quiet=True,  # Less verbose for tests
        server="waitress",  # or 'paste', 'gunicorn', etc.
    )


def test_server(server_and_args, subtests, capsys, base_url="http://localhost:5012"):
    """Test that each URL returns a valid HTTP status code.

    Since we already have test_smoke_web to test the underlying web
    renderers, here we only want/need to make sure that routing is working.
    """
    server, test_args = server_and_args

    urls = []
    for o_tool in test_args.tools.tools():
        tool = o_tool.name

        # Make sure we can get to the "base" display.
        urls.append(f"{base_url}/{tool}")

        # Now, make sure we can display each project as well
        for project in Project.select():
            partial = f"partials/set_project/{tool}?project={project.id}"
            urls.append(f"{base_url}/{partial}")

    for url in urls:
        with subtests.test(url):
            try:
                with urlopen(url, timeout=30) as response:
                    status_code = response.getcode()
                    assert 200 <= status_code < 400, f"Unexpected status from {url}: {status_code}"

            except HTTPError as exc:
                assert exc.code < 500, f"Server error at {url}: {exc.code}"

            except URLError as exc:
                pytest.fail(f"Connection failed for {url}: {str(exc.reason)}")
