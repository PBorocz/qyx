"""."""

import logging
import yaml
from argparse import ArgumentParser, Namespace
from pathlib import Path
from platformdirs import user_config_dir


from mq.utils.scoring import get_nested_config


log = logging.getLogger(__name__)


def setup_configuration(app_name: str = "mq") -> tuple[ArgumentParser, list[str], dict]:
    configuration_parser = ArgumentParser(add_help=False)
    configuration_parser.add_argument("-c", "--config", type=Path)
    config_args, remaining_args = configuration_parser.parse_known_args()  # Note method used here!

    if config_args.config:
        configuration = _load_config(config_args.config)
    else:
        configuration = _find_and_load_config(app_name)

    # Irrespective of which source, return the parser and configuration settings (if any!)
    return configuration_parser, remaining_args, configuration


def _load_config(config_path: Path | None) -> dict:
    """Load user's configuration from the specified path."""
    if not config_path:
        return {}

    if not config_path.exists():
        raise FileNotFoundError(f"Sorry, we couldn't find a configuration file at: {config_path}")

    with open(config_path, "rb") as fh_:
        return yaml.safe_load(fh_)


def _find_and_load_config(app_name: str, filename: str = "config.yaml") -> dict:
    """Find and load config from either of two possible locations: `cwd` and user config dir."""
    # Current directory?
    current = Path.cwd() / filename
    if current.exists():
        return _load_config(current)

    # User config directory for our app?
    config_path = Path(user_config_dir(app_name)) / filename
    if config_path.exists():
        return _load_config(config_path)

    return {}


def validate_config(args: Namespace) -> bool:
    """Return true if configuration validates."""
    # Primarily, we're checking that any tools mentioned are VALID against the tools we have defined."""
    error_encountered = False
    config = args.config

    # Dashboard layout..
    for tool_name in get_nested_config(config, "dashboard.tool_order"):
        if tool_name not in args.tools:
            log.error(f"Sorry, encountered {tool_name=} in 'dashboard.tool_order' section that isn't available!")
            error_encountered = True

    # UI layout..
    for tool_name in get_nested_config(config, "ui.tool_order"):
        if tool_name not in args.tools:
            log.error(f"Sorry, encountered {tool_name=} in 'ui.tool_order' section that isn't available!")
            error_encountered = True

    # Tool definitions
    for tool_name in config.get("tools", ()):
        if tool_name not in args.tools:
            log.error(f"Sorry, encountered {tool_name=} in 'tools' section that isn't available!")
            error_encountered = True

    return not error_encountered
