"""User state management/persistence."""

import json
import logging
from pathlib import Path
from platformdirs import user_state_dir

log = logging.getLogger(__name__)


STATE_FILE = Path(user_state_dir("mq")) / "state.json"
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)


def update_state(**kwargs):
    """Update state and persist automatically."""
    state = load_state()
    for key, value in kwargs.items():
        state[key] = value
        # log.debug(f"Set state {key=} to {value=}")
    save_state(state)


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
