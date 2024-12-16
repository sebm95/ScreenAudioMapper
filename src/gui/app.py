# src/gui/app.py
import tkinter as tk
from tkinter import ttk
import threading
import logging
from config.settings import load_config, save_config
from audio.audio_service import AudioService
from window.window_utils import WindowUtils
from services.monitor_service import start_monitor
from services.helpers import update_pid_mapping

logger = logging.getLogger(__name__)


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Screen to Audio Device Mapper")
        self.refresh_lists()
        
        self.config = load_config()
        
        self.pid_to_device = update_pid_mapping({}, self.config)
        
        self.monitoring_thread = None
        self.stop_event = threading.Event()
        
        if self.config:
            self.start_monitoring()
        
        self.create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def start_monitoring(self):
        self.monitoring_thread = threading.Thread(target=start_monitor, 
                                                  args=(self.config, 
                                                        self.pid_to_device, 
                                                        self.stop_event), 
                                                  daemon=True)
        self.monitoring_thread.start()
    
    def refresh_lists(self):
        self.screens = WindowUtils.detect_screens()
        self.audio_devices = list(AudioService.get_all_output_devices().keys())

    def create_widgets(self):
        tk.Label(self.root, text="Screen").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        tk.Label(self.root, text="Audio Device").grid(row=0, column=1, padx=10, pady=10, sticky="w")
        tk.Label(self.root, text="Volume").grid(row=0, column=2, padx=10, pady=10, sticky="w")

        self.mappings = {}
        self.volume_sliders = {}

        for i, screen in enumerate(self.screens):
            tk.Label(self.root, text=screen["name"]).grid(row=i + 1, column=0, padx=10, pady=5, sticky="w")

            device_var = tk.StringVar(value=self.config.get(screen["name"], ""))
            self.mappings[screen["name"]] = device_var

            device_dropdown = ttk.Combobox(self.root, textvariable=device_var, values=self.audio_devices, state="readonly")
            device_dropdown.grid(row=i + 1, column=1, padx=10, pady=5, sticky="w")
            device_dropdown.bind('<<ComboboxSelected>>', lambda e, s=screen["name"]: self.on_device_change(s))
            
            current_volume = 0
            if device_var.get():
                device_map = AudioService.get_all_output_devices()
                device_id = device_map.get(device_var.get())
                if device_id:
                    current_volume = AudioService.get_device_volume(device_id)
            else:
                current_volume = 0

            volume_slider = ttk.Scale(
                self.root,
                from_=0,
                to=100,
                orient="horizontal",
                value=current_volume,
                command=lambda v, s=screen["name"]: self.on_volume_change(s, v)
            )
            volume_slider.grid(row=i + 1, column=2, padx=10, pady=5, sticky="ew")
            self.volume_sliders[screen["name"]] = volume_slider

            volume_label = tk.Label(self.root, text=f"{current_volume}%")
            volume_label.grid(row=i + 1, column=3, padx=5, pady=5, sticky="w")
            self.volume_sliders[f"{screen['name']}_label"] = volume_label

        save_button = tk.Button(self.root, text="Apply", command=self.save_mappings)
        save_button.grid(row=len(self.screens) + 1, column=0, pady=10)

        refresh_button = tk.Button(self.root, text="Refresh Devices", command=self.refresh_devices)
        refresh_button.grid(row=len(self.screens) + 1, column=1, pady=10)

        self.status_label = tk.Label(self.root, text="")
        self.status_label.grid(row=len(self.screens) + 2, column=0, columnspan=4, pady=5)

    def on_volume_change(self, screen_name, volume):
        try:
            volume = float(volume)
            device_name = self.mappings[screen_name].get()
            if device_name:
                device_map = AudioService.get_all_output_devices()
                device_id = device_map.get(device_name)
                if device_id:
                    AudioService.set_device_volume(device_id, volume)
                    self.volume_sliders[f"{screen_name}_label"].config(text=f"{int(volume)}%")
        except Exception as e:
            self.status_label.config(text=f"Error setting volume: {str(e)}")

    def on_device_change(self, screen_name):
        try:
            device_name = self.mappings[screen_name].get()
            if device_name:
                device_map = AudioService.get_all_output_devices()
            device_id = device_map.get(device_name)
            if device_id:
                current_volume = AudioService.get_device_volume(device_id)
                self.volume_sliders[screen_name].set(current_volume)
                self.volume_sliders[f"{screen_name}_label"].config(text=f"{current_volume}%")
        except Exception as e:
            self.status_label.config(text=f"Error updating volume: {str(e)}")

    def save_mappings(self):
        for screen, device_var in self.mappings.items():
            self.config[screen] = device_var.get()
        save_config(self.config)

        if self.monitoring_thread is not None:
            self.stop_event.set()
            self.monitoring_thread.join()

        self.pid_to_device = update_pid_mapping(self.pid_to_device, self.config)

        self.stop_event.clear()

        self.start_monitoring()

    def refresh_devices(self):
        current_volumes = {screen: slider.get() for screen, slider in self.volume_sliders.items() if isinstance(slider, ttk.Scale)}
        current_mappings = {screen: var.get() for screen, var in self.mappings.items()}
        
        for widget in self.root.grid_slaves():
            widget.destroy()
        
        self.refresh_lists()
        self.create_widgets()
        
        for screen, device in current_mappings.items():
            if screen in self.mappings:
                if device in self.audio_devices:
                    self.mappings[screen].set(device)
                    if screen in current_volumes and screen in self.volume_sliders:
                        self.volume_sliders[screen].set(current_volumes[screen])
                else:
                    self.mappings[screen].set('')
                    if screen in self.config:
                        del self.config[screen]
        
        save_config(self.config)
        self.status_label.config(text="Devices refreshed successfully!")

    def on_closing(self):
        self.stop_event.set()
        if self.monitoring_thread is not None:
            self.monitoring_thread.join()
        self.root.destroy()