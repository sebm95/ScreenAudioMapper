# src/window/window_utils.py
from typing import List, Dict, Tuple
import logging

import win32gui
import win32process
import win32api

logger = logging.getLogger(__name__)

class WindowUtils:
    @staticmethod
    def get_active_monitors() -> List[Tuple[int, int, Tuple[int, int, int, int]]]:
        """Return a list of monitors with their handle, DC handle, and rect."""
        return win32api.EnumDisplayMonitors()

    @staticmethod
    def detect_screens() -> List[Dict[str, any]]:
        """Detect screens and return a list of screen dictionaries."""
        screens = []
        monitors = WindowUtils.get_active_monitors()
        for idx, (handle, dc_handle, rect) in enumerate(monitors):
            monitor_info = win32api.GetMonitorInfo(handle)
            device_name = monitor_info['Device']
            screen_name = f"Screen{idx+1}"
            screens.append({"name": screen_name, "position": rect, "device_name": device_name})
        return screens

    @staticmethod
    def get_active_window() -> Tuple[int, str, int, str]:
        """Get the active window and return a tuple of the PID, title, and screen name."""
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        monitor_info = win32api.GetMonitorInfo(win32api.MonitorFromWindow(hwnd))
        return pid, title, WindowUtils.screen_name_from_display(monitor_info['Device'])

    @staticmethod
    def screen_name_from_display(display_name: str) -> str:
        """Get the screen name from the display name."""
        base_name = display_name.replace('\\\\.\\', '')  # e.g., 'DISPLAY1'
        if "DISPLAY" in base_name:
            num_part = ''.join(filter(str.isdigit, base_name))
            if num_part.isdigit():
                return "Screen" + num_part
        return None
    
    @staticmethod
    def get_hwnd_from_pid(pid: int) -> int:
        """Get the window handle from the PID."""
        def callback(hwnd, hwnds):
            if win32gui.IsWindowVisible(hwnd):
                _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                if found_pid == pid:
                    hwnds.append(hwnd)
            return True
        
        hwnds = []
        win32gui.EnumWindows(callback, hwnds)
        return hwnds[0] if hwnds else None
        
    @staticmethod
    def get_window_screen(pid: int) -> str:
        """Get the screen name from the PID."""
        hwnd = WindowUtils.get_hwnd_from_pid(pid)
        monitor_info = win32api.GetMonitorInfo(win32api.MonitorFromWindow(hwnd))
        return WindowUtils.screen_name_from_display(monitor_info['Device'])
    
    @staticmethod
    def get_screen_pids() -> dict:
        """Get the screen name from the PID."""
        screen_pids = {}

        def enum_window_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    screen_name = WindowUtils.get_window_screen(pid)
                    if screen_name:
                        screen_pids[pid] = screen_name
                except Exception as e:
                    print(f"Error processing window handle {hwnd}: {e}")

        win32gui.EnumWindows(enum_window_callback, None)
        return screen_pids