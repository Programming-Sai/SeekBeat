from ..models import DeviceProfile
from django.utils import timezone

class DeviceManager:
    """
    Manages registration, reconnection, disconnection, and listing of devices
    within an active LAN session.
    """
    def handshake(self, device_data: dict, access_code: str, system_access_code: str, ip_address: str) -> tuple[dict, int]:
        """
        Register a new device or update an existing one in the active LAN session.

        Args:
            device_data (dict): {
                "device_name": str,
                "os_version": str,
                "ram_mb": int,
                "storage_mb": int,
                "device_id": str (optional, UUID format)
            }
            access_code (str): The code provided by the client in headers.
            system_access_code (str): The code stored on the server for this session.

        Returns:
            tuple: (response_dict, http_status)
                response_dict: {
                    "device_id": str,
                    "message": str
                }
                http_status: 200 on success, 400 on name conflict.

        Raises:
            PermissionError: If access_code is missing or does not match.
        """
        if access_code and system_access_code and access_code == system_access_code:
            device_name = device_data.get("device_name")
            os_version = device_data.get("os_version")
            ram_mb = device_data.get("ram_mb")
            storage_mb = device_data.get("storage_mb")
            device_id = device_data.get("device_id")


            if DeviceProfile.objects.filter(device_name=device_name).exclude(device_id=device_id).exists():
                    return {"error": f"Device name '{device_name}' already in use."}, 400
            

            # Try to find an existing active device with same name and OS
            device = DeviceProfile.objects.filter(device_id=device_id).first()


            if device:
                # Update stats
                device.device_name = device_name
                device.ram_mb = ram_mb
                device.storage_mb = storage_mb
                device.last_seen = timezone.now()
                device.is_active = True
                device.ip_address = ip_address
                device.save()
                created = False
            else:
                # Create new device
                device = DeviceProfile.objects.create(
                    device_name=device_name,
                    os_version=os_version,
                    ram_mb=ram_mb,
                    ip_address =ip_address,
                    storage_mb=storage_mb
                )
                created = True

            return {
                "device_id": str(device.device_id),
                "message": f"{device.device_name} registered" if created else f"{device.device_name} updated"
            }, 200
        else:
            raise PermissionError("Invalid access code. Please Provide a valid Access Code")


    def reconnect(self, device_data: dict, access_code: str, system_access_code: str) -> tuple[dict, int]:
        """
        Reactivate a previously disconnected device in the active LAN session.

        Args:
            device_data (dict): {"device_id": str (UUID format)}
            access_code (str): The code provided by the client in headers.
            system_access_code (str): The code stored on the server for this session.

        Returns:
            tuple: (response_dict, http_status)
                response_dict: {
                    "device_id": str,
                    "message": str
                }
                http_status: 200 on success.

        Raises:
            PermissionError: If access_code is missing or invalid.
            ValueError: If device_id does not correspond to any DeviceProfile.
        """
        if access_code and system_access_code and access_code == system_access_code:
            device_id = device_data.get("device_id")


            device = DeviceProfile.objects.filter(device_id=device_id).first()


            if device:
                device.is_active = True
                device.save()
            else:
                raise ValueError(f"A device with id: {device_id} does not exist.")


            return {
                "device_id": str(device.device_id),
                "message": f"{device.device_name} reconnected"
            }, 200
        else:
            raise PermissionError("Invalid access code. Please Provide a valid Access Code")


 

    def disconnect(self, device_id: str, keep_data: bool = False) -> tuple[dict, int]:
        """
        Disconnect a device from the LAN session.

        Args:
            device_id (str): UUID of the device to disconnect.
            keep_data (bool): If True, retain the DeviceProfile and its songs;
                              if False, delete the device record entirely.

        Returns:
            tuple: (response_dict, http_status)
                response_dict: {
                    "message": str,
                    "device_id": str
                }
                http_status: 200 on success, 404 if device not found.
        """
        try:
            device = DeviceProfile.objects.get(device_id=device_id)
        except DeviceProfile.DoesNotExist:
            return {"error": "Device not found"}, 404
        
        if keep_data:
            device.is_active = False
            device.keep_data_on_leave = True
            device.save()
        else:
            device.delete()

        return {"message": f"{device.device_name} disconnected", "device_id": str(device_id)}, 200




    def get_active_devices(self, access_code: str, system_access_code: str) -> tuple[tuple[list, int], int]:
        """
        Retrieve all currently active devices in the session.

        Args:
            access_code (str): The code provided by the client in headers.
            system_access_code (str): The code stored on the server for this session.

        Returns:
            tuple: (
                [devices_list, count], http_status
            )
            devices_list: list of {
                "device_id": str,
                "device_name": str,
                "os_version": str,
                "ram_mb": int or None,
                "storage_mb": int or None,
                "last_seen": str (ISO8601) or None
            }
            count: number of active devices
            http_status: 200 on success, 403 if access code invalid.
        """
        if access_code != system_access_code:
            return {"error": "Invalid access code."}, 403

        devices = DeviceProfile.objects.filter(is_active=True)
        devices_data = [
            {
                "device_id": str(d.device_id),
                "device_name": d.device_name,
                "os_version": d.os_version,
                "ram_mb": d.ram_mb,
                "storage_mb": d.storage_mb,
                "last_seen": d.last_seen.isoformat() if d.last_seen else None
            }
            for d in devices
        ]
        return (devices_data, len(devices_data)), 200