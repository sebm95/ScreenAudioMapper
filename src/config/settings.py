# src/config/settings.py
import json
import os
from typing import Dict
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

CONFIG_FILE = Path(__file__).resolve().parents[2] / 'screen_audio_mapping.json'


def load_config() -> Dict[str, str]:
    """Load configuration from the JSON file."""
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Config file not found: {CONFIG_FILE}")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Config file is empty or corrupted: {CONFIG_FILE}. Returning default configuration.")
        return {}

def save_config(config: Dict[str, str]):
    """Save configuration to the JSON file."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)