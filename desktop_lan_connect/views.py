import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample
from .lan_utils.initialization import LANCreator
from django_ratelimit.decorators import ratelimit
from .lan_utils.device_manager import DeviceManager


logger = logging.getLogger('seekbeat')
handler = logging.getLogger('seekbeat').handlers[0]
handler.doRollover()


lan = LANCreator()
device_manager = DeviceManager()



@extend_schema(
    summary="Start Local Network Session",
    description="Generates a QR code to join a local session. Optionally override an existing session.",
    parameters=[
        OpenApiParameter(
            name="override",
            description="Whether to terminate and recreate an existing session (true/false).",
            required=False,
            type=bool,
            location=OpenApiParameter.QUERY
        )
    ],
    responses={
        200: OpenApiResponse(description="QR code path returned", examples=[
            OpenApiExample(
                name="Session Started",
                summary="Successful response",
                value={"qr_path": "/path/to/qr_code.png"},
                response_only=True
            )
        ]),
        400: OpenApiResponse(description="Session already exists or error occurred", examples=[
            OpenApiExample(
                name="Session Already Exists",
                summary="Attempt to start without override",
                value={"error": "Session already exists. Use override to force new session."},
                response_only=True
            )
        ])
    },
    methods=["GET"],
    tags=["LAN Session Manager"]
)
@api_view(["GET"])
def start_lan_session_view(request):
    allow_override = request.GET.get("override", "false").lower() == "true"

    try:
        qr_path, _ = lan.initialize_session(allow_override=allow_override)
        return Response({"qr_path": qr_path})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# http://localhost:8000/api/lan/session-start/ OR
# http://localhost:8000/api/lan/session-start/?override=true



@extend_schema(
    summary="Check LAN Session Status",
    description="Returns whether a LAN session is currently active.",
    responses={
        200: OpenApiResponse(description="Session status", examples=[
            OpenApiExample(name="Active", value={"active": True, "access_code": "abcd-1234"}),
            OpenApiExample(name="Inactive", value={"active": False})
        ]),
        500: OpenApiResponse(description="Internal server error")
    },
    methods=["GET"],
    tags=["LAN Session Manager"]
)
@api_view(["GET"])
@ratelimit(key='ip', rate='10/m', block=True)
def check_lan_session_status(request):
    try:
        isActive = lan.has_active_session()
        if isActive:
            return Response({"active": True })
        return Response({"active": False})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# http://localhost:8000/api/lan/session-check/



@extend_schema(
    summary="Terminate LAN Session",
    description="Terminates the currently active LAN session and removes the QR code. Requires the 'Access-Code' header for authentication.",
    parameters=[
        OpenApiParameter(
            name="Access-Code",
            type=str,
            location=OpenApiParameter.HEADER,
            required=True,
            description="Access code required to authorize session termination."
        )
    ],
    responses={
        200: OpenApiResponse(description="Session terminated", examples=[
            OpenApiExample(name="Success", value={"message": "Session terminated."})
        ]),
        400: OpenApiResponse(description="No active session", examples=[
            OpenApiExample(name="None", value={"error": "No active session found."})
        ]),
        500: OpenApiResponse(description="Internal server error")
    },
    methods=["POST"],
    tags=["LAN Session Manager"]
)
@api_view(["POST"])
@ratelimit(key='ip', rate='10/m', block=True)
def terminate_lan_session(request):
    access_code = request.headers.get("Access-Code")
    try:
        isActive = lan.has_active_session()
        session_data = lan.get_session_data()
        if not isActive:
            return Response({"error": "No active session found."}, status=status.HTTP_400_BAD_REQUEST)

        qr_path = session_data.get("qr_path")
        res = lan.terminate_session(qr_path, access_code)

        return Response(res)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# http://localhost:8000/api/lan/session-end/ With the Access-Code HEADER which would just be the access code











@extend_schema(
    summary="Connect or Update Device",
    description="""
Registers a new device to the active LAN session or updates an existing one.

- The request must include a valid **Access-Code** in the request headers.
- Device names must be unique across the session.
- If a `device_id` is included and matches an existing device, that device will be **reactivated** and its system info (RAM, storage, etc.) updated. This also supports reconnecting previously disconnected devices.
- If no device exists with the provided name or ID, a new one is created.
- This operation is only allowed if there is an active LAN session.

**Headers:**
- `Access-Code`: The session's access code.

**Returns:**
- A `device_id` and a message indicating whether the device was created or updated.
""",
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "device_name": {"type": "string"},
                "os_version": {"type": "string"},
                "ram_mb": {"type": "integer"},
                "storage_mb": {"type": "integer"},
                "device_id": {"type": "string", "nullable": True}
            },
            "required": ["device_name", "os_version", "ram_mb", "storage_mb"]
        }
    },
    responses={
        200: OpenApiResponse(description="Device registered or updated", examples=[
            OpenApiExample(
                name="Success",
                value={
                    "device_id": "abc123",
                    "message": "Device connected successfully."
                }
            )
        ]),
        403: OpenApiResponse(description="Forbidden (No active LAN session or invalid access code)", examples=[
            OpenApiExample(
                name="No Session",
                value={"error": "No active LAN session. Cannot register device."}
            ),
            OpenApiExample(
                name="Bad Access Code",
                value={"error": "Invalid access code."}
            )
        ]),
        500: OpenApiResponse(description="Internal server error")
    },
    methods=["POST"],
    tags=["LAN Device Manager"]
)
@api_view(["POST"])
def device_handshake_view(request):
    try:
        data = request.data
        if not lan.has_active_session(): 
            return Response( {"error": "No active LAN session. Cannot register device."}, status=status.HTTP_403_FORBIDDEN)
        
        access_code = request.headers.get("Access-Code")
        system_access_code = lan.get_session_data()["access_code"]
        result, status_ = device_manager.handshake(data, access_code, system_access_code)
        return Response(result, status=status_)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# http://localhost:8000/api/lan/device-connect/ With the Access-Code HEADER which would just be the access code




@extend_schema(
    summary="Reconnect Device",
    description=(
        "Reactivates a previously disconnected device by its device ID. "
        "Requires an active LAN session and a valid access code in the headers. "
        "Reconnection will update the device's last seen timestamp and set it as active."
    ),
    parameters=[
        OpenApiParameter(
            name="Access-Code",
            type=str,
            location=OpenApiParameter.HEADER,
            required=True,
            description="Access code required to authorize reconnection."
        )
    ],
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "device_id": {"type": "string"}
            },
            "required": ["device_id"]
        }
    },
    responses={
        200: OpenApiResponse(
            description="Device reconnected successfully",
            examples=[OpenApiExample(
                name="Success",
                value={"message": "Device reconnected", "device_id": "abc123"}
            )]
        ),
        400: OpenApiResponse(
            description="Invalid device ID",
            examples=[OpenApiExample(
                name="Not Found",
                value={"error": "Device not found"}
            )]
        ),
        403: OpenApiResponse(
            description="No active LAN session or invalid access code",
            examples=[OpenApiExample(
                name="Forbidden",
                value={"error": "No active session or invalid access code"}
            )]
        ),
        500: OpenApiResponse(description="Internal server error"),
    },
    methods=["POST"],
    tags=["LAN Device Manager"]
)
@api_view(["POST"])
def device_reconnect_view(request):
    try:
        data = request.data
        if not lan.has_active_session(): 
            return Response( {"error": "No active LAN session. Cannot register device."}, status=status.HTTP_403_FORBIDDEN)
        
        access_code = request.headers.get("Access-Code")
        system_access_code = lan.get_session_data()["access_code"]
        result, status_ = device_manager.reconnect(data, access_code, system_access_code)
        return Response(result, status=status_)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# http://localhost:8000/api/lan/device-reconnect/ With the Access-Code HEADER which would just be the access code





@extend_schema(
    summary="Disconnect Device",
    description="Disconnects a device using its ID. Optionally keep device data for future reconnection.",
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "device_id": {"type": "string"},
                "keep_data": {"type": "boolean"}
            },
            "required": ["device_id"]
        }
    },
    responses={
        200: OpenApiResponse(description="Device disconnected", examples=[
            OpenApiExample(name="Success", value={"message": "Device removed from LAN session."})
        ]),
        400: OpenApiResponse(description="Device not found", examples=[
            OpenApiExample(name="Invalid", value={"error": "No such device connected."})
        ]),
        500: OpenApiResponse(description="Internal server error")
    },
    methods=["POST"],
    tags=["LAN Device Manager"]
)
@api_view(["POST"])
def device_disconnect_view(request):
    try:
        device_id = request.data.get("device_id")
        keep_data = request.data.get("keep_data", True)
        result, code = device_manager.disconnect(device_id, keep_data)
        return Response(result, status=code)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# http://localhost:8000/api/lan/device-disconnect/




@extend_schema(
    summary="List Active Devices",
    description="Returns a list of devices currently active in the LAN session.",
    parameters=[
        OpenApiParameter(
            name="Access-Code",
            type=str,
            location=OpenApiParameter.HEADER,
            required=True,
            description="Access code required to retrieve active devices."
        )
    ],
    responses={
        200: OpenApiResponse(
            description="List of active devices",
            examples=[
                OpenApiExample(
                    name="Success",
                    value={
                        "devices": [
                            {
                                "device_id": "abc123",
                                "device_name": "Isaiah's Laptop",
                                "os_version": "Windows 10",
                                "ram_mb": 8192,
                                "storage_mb": 256000,
                                "last_seen": "2025-05-24T09:00:00Z"
                            },
                            # More devices ...
                        ]
                    }
                )
            ]
        ),
        403: OpenApiResponse(description="No active session or invalid access code"),
        500: OpenApiResponse(description="Internal server error")
    },
    methods=["GET"],
    tags=["LAN Device Manager"]
)
@api_view(["GET"])
def active_devices_view(request):
    try:
        if not lan.has_active_session():
            return Response({"error": "No active LAN session."}, status=status.HTTP_403_FORBIDDEN)
        
        access_code = request.headers.get("Access-Code")
        system_access_code = lan.get_session_data()["access_code"]
        devices_data, status_ = device_manager.get_active_devices(access_code, system_access_code)
        return Response({"count":devices_data[1], "devices": devices_data[0]}, status=status_)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# http://localhost:8000/api/lan/devices/ With the Access-Code HEADER which would just be the access code