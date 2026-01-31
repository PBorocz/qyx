"""..."""

import socket
import threading
import time
from argparse import Namespace
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

import pytest
import uvicorn

from mq.tools.base import Project
from mq.setup.args_configuration import setup_configuration
from mq.setup.logging import setup_logging
from mq.setup.sqlite import setup_sqlite
from mq.setup.tools import setup_tools
from mq.web.serve import create_app, register


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
def test_server_args():
    # Base URL for your local web service
    port = 5012
    base_url = f"http://localhost:{port}"

    """Start the web server before tests and stop it after."""
    # Check if server is already running
    if is_port_in_use(port):
        pytest.skip(f"Port {port} is already in use. Using existing server.")
        yield
        return

    # Create args for your server
    args = Namespace(port=port, browser=False, log_level="info")
    _, _, configuration = setup_configuration()
    setup_logging(args.log_level)
    setup_tools(args)
    setup_sqlite(args)
    args.config = configuration

    # Create the app
    global app, rt
    app, rt = create_app(args)
    register(args, rt)

    # Setup uvicorn
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=port,
        log_level="warning",  # Less verbose for tests
        access_log=True,
        use_colors=True,
        ws="websockets-sansio",  # Use this to avoid websockets.legacy deprecation (https://github.com/Kludex/uvicorn/discussions/2476)
    )
    server = uvicorn.Server(config)

    # ...and run it a background thread (thanks Claude!)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    health_url = f"{base_url}/health"
    if not wait_for_server(health_url, timeout=20):
        pytest.fail("Server failed to start within timeout")
    print(f"\n↑ Test server successfully started ({port=})")

    time.sleep(1)
    yield (server, args)

    # Cleanup: shutdown server
    print(f"\n↓ Test server shut down ({port=})")
    server.should_exit = True


def test_server(test_server_args, subtests, capsys, base_url="http://localhost:5012"):
    """Test that each URL returns a valid HTTP status code.

    Since we already have test_smoke_web to test the underlying web renderers, here
    we only want/need to make sure that routing is working.
    """
    server, test_args = test_server_args
    # urls = []
    # for project in Project.select():
    #     urls.append(f"{base_url}/{project.id}")
    # urls.append(base_url)

    urls = []
    for o_tool in test_args.tools.values():
        tool = o_tool.module_name

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
