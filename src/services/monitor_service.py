# src/services/monitor_service.py
import threading
import logging

from audio.audio_service import AudioService
from window.window_utils import WindowUtils

logger = logging.getLogger(__name__)

POLLING_INTERVAL = 0.1  # seconds


def _monitor_loop(config: dict, pid_to_device: dict, stop_event: threading.Event):
    logger.info("Starting monitor loop")
    device_map = AudioService.get_all_output_devices()
    
    while not stop_event.is_set():
        try:
            pid, title, current_display_name = WindowUtils.get_active_window()

            if current_display_name and current_display_name in config and config[current_display_name]:
                target_device_name = config[current_display_name]
                target_device_id = device_map[target_device_name]

                if pid not in pid_to_device or pid_to_device[pid] != target_device_id:
                    logger.info(f"Updating audio device for PID {pid} on display {current_display_name}")
                    pid_to_device[pid] = target_device_id
                    AudioService.set_application_output_device(pid, target_device_id)

            stop_event.wait(POLLING_INTERVAL)

        except Exception as e:
            logger.error(f"Error in monitor loop: {str(e)}")
            stop_event.wait(POLLING_INTERVAL)

def start_monitor(config: dict, pid_to_device: dict, stop_event: threading.Event) -> threading.Thread:
    monitor_thread = threading.Thread(target=_monitor_loop, args=(config, pid_to_device, stop_event))
    monitor_thread.daemon = True
    monitor_thread.start()
    return monitor_thread


if __name__ == "__main__":
    start_monitor()

