# src/config/settings.py
import json
import os
from typing import Dict
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

CONFIG_FILE = Path(__file__).resolve().parents[2] / 'screen_audio_mapping.json'


def load_config() -> Dict[str, str]:
    """Load configuration from the JSON file and validate against available devices."""
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        
        from audio.audio_service import AudioService
        available_devices = AudioService.get_all_output_devices()
        
        valid_config = {
            screen: device 
            for screen, device in config.items() 
            if device in available_devices.keys()
        }
        
        if valid_config != config:
            logger.warning("Some configured devices are no longer available. Cleaning up config.")
            save_config(valid_config)
            
        return valid_config
            
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