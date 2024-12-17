# src/audio/audio_service.py
from ctypes import POINTER, cast, CDLL
import logging
import pythoncom
import comtypes
from pathlib import Path
from comtypes import CLSCTX_ALL
from pycaw.constants import CLSID_MMDeviceEnumerator
from pycaw.pycaw import (
    DEVICE_STATE,
    AudioUtilities,
    EDataFlow,
    ERole,
    IAudioEndpointVolume,
    IMMDeviceEnumerator,
)

logger = logging.getLogger(__name__)

audioDll = CDLL("./src/audio/AudioDLL.dll")


class COMContextManager:
    """Context manager for COM initialization and uninitialization."""

    def __enter__(self):
        pythoncom.CoInitialize()

    def __exit__(self, exc_type, exc_value, traceback):
        pythoncom.CoUninitialize()


class AudioService:
    @staticmethod
    def get_all_output_devices() -> dict:
        """Get all active output devices."""
        devices = {}

        with COMContextManager():
            device_enumerator = comtypes.CoCreateInstance(
                CLSID_MMDeviceEnumerator,
                IMMDeviceEnumerator,
                comtypes.CLSCTX_INPROC_SERVER,
            )
            if not device_enumerator:
                logger.error("Failed to create device enumerator.")
                return devices

            collection = device_enumerator.EnumAudioEndpoints(
                EDataFlow.eRender.value, DEVICE_STATE.ACTIVE.value
            )
            if not collection:
                logger.error("No active audio endpoints found.")
                return devices

            for i in range(collection.GetCount()):
                device = collection.Item(i)
                if device:
                    device_object = AudioUtilities.CreateDevice(device)
                    if ": None" not in str(device_object):
                        devices[device_object.FriendlyName] = device_object.id
                    device_object._dev.Release()

        return devices

    @staticmethod
    def set_application_output_device(pid: int, device_id: str) -> None:
        """Set the output device for a specific application."""
        with COMContextManager():
            try:
                result = audioDll.SetApplicationEndpoint(device_id, 0, pid)
                if result != 0:
                    logger.error(f"Failed to change audio device for pid: {pid}, app might not have sound")
            except Exception as e:
                logger.error(f"Error changing audio device: {e}")

    @staticmethod
    def get_device_volume(device_id: str) -> float:
        """Get the volume level of a specific device."""
        with COMContextManager():
            try:
                device_object = AudioService.get_device_object(device_id)
                if not device_object:
                    logger.warning(f"Device with ID {device_id} not found.")
                    return 0.0

                volume = cast(device_object, POINTER(IAudioEndpointVolume))
                vol_level = volume.GetMasterVolumeLevelScalar()
                result = round(vol_level * 100)
                # Explicitly release COM objects
                volume.Release()
                device_object.Release()
                return result
            except Exception as e:
                logger.error(f"Error getting volume: {e}")
                return 0.0
            finally:
                # Ensure we attempt to release objects even if an error occurred
                try:
                    if 'volume' in locals():
                        volume.Release()
                    if 'device_object' in locals():
                        device_object.Release()
                except:
                    pass

    @staticmethod
    def set_device_volume(device_id: str, volume_level: float) -> None:
        """Set the volume level of a specific device."""
        with COMContextManager():
            try:
                device_object = AudioService.get_device_object(device_id)
                if not device_object:
                    logger.warning(f"Device with ID {device_id} not found.")
                    return

                volume = cast(device_object, POINTER(IAudioEndpointVolume))
                scalar_volume = max(0.0, min(volume_level / 100, 1.0))
                volume.SetMasterVolumeLevelScalar(scalar_volume, None)
                # Explicitly release COM objects
                volume.Release()
                device_object.Release()
            except Exception as e:
                logger.error(f"Error setting volume: {e}")
            finally:
                # Ensure we attempt to release objects even if an error occurred
                try:
                    if 'volume' in locals():
                        volume.Release()
                    if 'device_object' in locals():
                        device_object.Release()
                except:
                    pass

    @staticmethod
    def get_device_object(device_id: str):
        """Get the device object for a specific device ID."""
        with COMContextManager():
            try:
                device_enumerator = comtypes.CoCreateInstance(
                    CLSID_MMDeviceEnumerator,
                    IMMDeviceEnumerator,
                    comtypes.CLSCTX_INPROC_SERVER,
                )
                if not device_enumerator:
                    logger.error("Failed to create device enumerator.")
                    return None

                collection = device_enumerator.EnumAudioEndpoints(
                    EDataFlow.eRender.value, DEVICE_STATE.ACTIVE.value
                )

                for device in collection:
                    if device.GetId() == device_id:
                        return device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)

            except Exception as e:
                logger.error(f"Error getting device object: {e}")
                return None

        return None
    
    @staticmethod
    def get_default_output_device():
        """Get the default output device."""
        STGM_READ = 0x00000000
        PKEY_Device_FriendlyName = "{a45c254e-df1c-4efd-8020-67d146a850e0} 14".upper()
        device = {}
        with COMContextManager():
            try:
                device_enumerator = comtypes.CoCreateInstance(
                    CLSID_MMDeviceEnumerator,
                    IMMDeviceEnumerator,
                    comtypes.CLSCTX_INPROC_SERVER)

                default_device = device_enumerator.GetDefaultAudioEndpoint(EDataFlow.eRender.value, ERole.eMultimedia.value)
                property_store = default_device.OpenPropertyStore(STGM_READ)

                for i in range(property_store.GetCount()):
                    prop_key = property_store.GetAt(i)
                    if str(prop_key) == PKEY_Device_FriendlyName:
                        value = property_store.GetValue(prop_key).GetValue()
                        device[value] = default_device.GetId()
                        return device
            except Exception as e:
                logger.error(f"Error getting default output device: {e}")
                return None

    @staticmethod
    def validate_device_id(device_id: str) -> bool:
        """Validate if a device ID still exists in the system."""
        with COMContextManager():
            try:
                device_enumerator = comtypes.CoCreateInstance(
                    CLSID_MMDeviceEnumerator,
                    IMMDeviceEnumerator,
                    comtypes.CLSCTX_INPROC_SERVER,
                )
                if not device_enumerator:
                    return False

                collection = device_enumerator.EnumAudioEndpoints(
                    EDataFlow.eRender.value, DEVICE_STATE.ACTIVE.value
                )
                
                for device in collection:
                    if device.GetId() == device_id:
                        return True
                return False
                
            except Exception as e:
                logger.error(f"Error validating device ID: {e}")
                return False