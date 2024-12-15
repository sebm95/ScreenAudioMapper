# src/services/helpers.py
import logging

from audio.audio_service import AudioService
from window.window_utils import WindowUtils

logger = logging.getLogger(__name__)


def get_pid_mapping(config: dict) -> dict:
    """Get the PID to device mapping from the config."""
    pid_to_device = {}
    pid_to_screen = WindowUtils.get_screen_pids()
    audio_devices = AudioService.get_all_output_devices()

    for pid, screen in pid_to_screen.items():
        if screen in config:
            target_device_name = config[screen]
            target_device_id = audio_devices[target_device_name]
            pid_to_device[pid] = target_device_id

    return pid_to_device


def update_pid_mapping(old_pid_to_device: dict, config: dict) -> dict:
    """Update the PID to device mapping."""
    new_pid_to_device = get_pid_mapping(config)

    if not old_pid_to_device:
        for pid, device in new_pid_to_device.items():
            AudioService.set_application_output_device(pid, device)
        return new_pid_to_device

    for pid, new_device in new_pid_to_device.items():
        if pid not in old_pid_to_device or old_pid_to_device[pid] != new_device:
            AudioService.set_application_output_device(pid, new_device)

    return new_pid_to_device