"""."""

import logging
import yaml
from argparse import ArgumentParser, Namespace
from pathlib import Path
from platformdirs import user_config_dir
from typing import Any


log = logging.getLogger(__name__)


class Configuration:
    """Simple encapsulation around our configuration entity (dict)."""

    def __init__(self, config: dict):
        """Setup a new configuration instance."""
        self.__configuration: dict[str, Any] = config

    def get(self, path: str, default: Any = None) -> Any:
        """Return the nested key's value from our internal configuration dictionary."""
        """Get nested config value using dot notation."""
        keys = path.split(".")
        value = self.__configuration
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        return value

    def validate(self, args: Namespace) -> bool:
        """Return true if configuration validates."""
        # Primarily, we're checking that any tools mentioned are VALID against the tools we have defined."""
        error_encountered = False

        # Tool definitions themselves..
        for tool_name in self.get("tools", ()):
            if tool_name not in args.tools:
                log.error(f"Sorry, encountered {tool_name=} in 'tools' section that isn't available!")
                error_encountered = True

        # Navbar layout of tool names..
        for tool_name in self.get("renderers.web.nav.tool_order", ()):
            if tool_name not in args.tools:
                msg = f"Sorry, encountered {tool_name=} in 'renderers.web.nav.tool_order' "
                +"section that isn't available!"
                log.error(msg)
                error_encountered = True

        # Dashboard layout of analyses..
        for tool_analysis in self.get("renderers.web.dashboard.analysis_order", ()):
            try:
                (tool, analysis) = tool_analysis.split(":")
            except ValueError:
                msg = f"Sorry, encountered {tool_analysis=} in 'renderers.web.dashboard.analysis_order' "
                +"section that isn't correctly formatted, should be '<tool>:<analysis>'!"
                log.error(msg)
                error_encountered = True

            if tool not in args.tools:
                msg = f"Sorry, encountered {tool=} in 'renderers.web.dashboard.analysis_order' "
                +"section that isn't available!"
                log.error(msg)
                error_encountered = True
            else:
                o_tool = args.tools[tool]
                analyses = [anl.lower() for anl in o_tool.analyses]
                if analysis.lower() not in analyses:
                    msg = (
                        (
                            f"Sorry, encountered {analysis=} in 'renderers.web.dashboard.analysis_order' "
                            f"section that isn't defined for {tool=}!"
                        ),
                    )
                    log.error(msg)
                    error_encountered = True

        return not error_encountered


def setup_configuration(app_name: str = "qyx") -> tuple[ArgumentParser, list[str], Configuration]:
    configuration_parser = ArgumentParser(add_help=False)
    configuration_parser.add_argument("-c", "--config", type=Path)
    config_args, remaining_args = configuration_parser.parse_known_args()

    if config_args.config:
        configuration = Configuration(_load_config(config_args.config))
    else:
        configuration = Configuration(_find_and_load_config(app_name))

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
