"""CLI configuration management - load, save, and query CLI configs."""

import json
import os
import uuid
from typing import List, Dict, Any, Optional
from .config import DATA_DIR

# Config file location (alongside conversations folder)
CONFIG_FILE = os.path.join(os.path.dirname(DATA_DIR), "cli_config.json")

# Default configuration
DEFAULT_CONFIG = {
    "clis": [
        {
            "id": "gemini",
            "name": "Gemini",
            "command": "gemini",
            "args": [],
            "enabled": True
        },
        {
            "id": "claude",
            "name": "Claude",
            "command": "claude",
            "args": ["-p"],
            "enabled": True
        },
        {
            "id": "codex",
            "name": "Codex",
            "command": "codex",
            "args": ["exec"],
            "enabled": True
        },
        {
            "id": "amp",
            "name": "Amp",
            "command": "amp",
            "args": ["-x"],
            "enabled": True
        }
    ],
    "chairman_id": "gemini",
    "council_ids": ["gemini", "claude", "codex", "amp"]
}


def load_config() -> Dict[str, Any]:
    """
    Load CLI configuration from JSON file.
    Returns default config if file doesn't exist.
    """
    if not os.path.exists(CONFIG_FILE):
        # Create default config file
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading config, using defaults: {e}")
        return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]) -> None:
    """
    Save CLI configuration to JSON file.
    Creates the data directory if it doesn't exist.
    """
    # Ensure directory exists
    config_dir = os.path.dirname(CONFIG_FILE)
    if config_dir and not os.path.exists(config_dir):
        os.makedirs(config_dir)

    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


def get_active_clis() -> List[Dict[str, Any]]:
    """
    Get list of enabled CLIs in council order.
    Returns CLI configs for all enabled CLIs, ordered by council_ids.
    """
    config = load_config()
    clis_by_id = {cli["id"]: cli for cli in config["clis"]}

    active = []
    for cli_id in config.get("council_ids", []):
        if cli_id in clis_by_id:
            cli = clis_by_id[cli_id]
            if cli.get("enabled", True):
                active.append(cli)

    return active


def get_chairman() -> Optional[Dict[str, Any]]:
    """
    Get the chairman CLI config.
    Returns None if chairman not found or not enabled.
    """
    config = load_config()
    chairman_id = config.get("chairman_id")

    for cli in config["clis"]:
        if cli["id"] == chairman_id and cli.get("enabled", True):
            return cli

    return None


def get_cli_by_id(cli_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific CLI config by ID.
    """
    config = load_config()
    for cli in config["clis"]:
        if cli["id"] == cli_id:
            return cli
    return None


def generate_cli_id() -> str:
    """Generate a unique CLI ID."""
    return str(uuid.uuid4())[:8]


def validate_config(config: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate a configuration before saving.
    Returns (is_valid, error_message).
    """
    clis = config.get("clis", [])
    chairman_id = config.get("chairman_id")
    council_ids = config.get("council_ids", [])

    # Must have at least one CLI
    if not clis:
        return False, "At least one CLI is required"

    # Must have at least one enabled CLI
    enabled_clis = [c for c in clis if c.get("enabled", True)]
    if not enabled_clis:
        return False, "At least one CLI must be enabled"

    # Chairman must exist
    cli_ids = {c["id"] for c in clis}
    if chairman_id not in cli_ids:
        return False, f"Chairman '{chairman_id}' not found in CLIs"

    # Chairman must be enabled
    chairman = next((c for c in clis if c["id"] == chairman_id), None)
    if chairman and not chairman.get("enabled", True):
        return False, "Chairman must be enabled"

    # All CLIs must have name and command
    for cli in clis:
        if not cli.get("name"):
            return False, f"CLI '{cli.get('id', 'unknown')}' is missing a name"
        if not cli.get("command"):
            return False, f"CLI '{cli.get('name', 'unknown')}' is missing a command"

    return True, ""
