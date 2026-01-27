"""User state management/persistence."""

import json
import logging
from argparse import Namespace
from pathlib import Path
from platformdirs import user_state_dir

log = logging.getLogger(__name__)


STATE_FILE = Path(user_state_dir("mq")) / "state.json"  # On Mac: ~/Library/Application Support/mq
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)


def update_state(**kwargs):
    """Update state and persist automatically."""
    state = load_state()
    for key, value in kwargs.items():
        state[key] = value
        # log.debug(f"Set state {key=} to {value=}")
    save_state(state)


def update_state_from_args(args: Namespace) -> None:
    """Update state from our "args" namespace after we complete any command."""
    kwargs = dict()
    if "name" in args:
        kwargs["last_name"] = args.name
    if "tool_analysis" in args:
        kwargs["last_tool_analysis"] = args.tool_analysis
    update_state(**kwargs)


def save_state(state_dict: dict) -> None:
    """Save UI state to file."""
    STATE_FILE.write_text(json.dumps(state_dict, indent=2))
    # log.debug(f"Saved state to: {STATE_FILE=}")


def load_state() -> dict | None:
    """Load UI state from file."""
    if STATE_FILE.exists():
        # log.debug(f"Reading state from: {STATE_FILE=}")
        return json.loads(STATE_FILE.read_text())
    return {}
