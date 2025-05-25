import logging
from uuid import UUID
from django.core.exceptions import ValidationError, PermissionDenied
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample

from .serializers import SongProfileSerializer, SongUploadSerializer
from .lan_utils.device_manager import DeviceManager
from .lan_utils.song_manager import SongManager
from .lan_utils.initialization import LANCreator
from django_ratelimit.decorators import ratelimit


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

        return Response(res, status=200)
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
        ip_address = request.META.get('REMOTE_ADDR')
        if not lan.has_active_session(): 
            return Response( {"error": "No active LAN session. Cannot register device."}, status=status.HTTP_403_FORBIDDEN)
        
        access_code = request.headers.get("Access-Code")
        system_access_code = lan.get_session_data()["access_code"]
        result, status_ = device_manager.handshake(data, access_code, system_access_code, ip_address)
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
        SongManager.delete_uploaded_files_for_device(UUID(device_id))
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





@extend_schema(
    operation_id="list or delete_all_device_songs",
    summary="List or Delete All Songs for Device",
    description="GET fetches all songs for a device. DELETE removes all songs for a device.",
    responses={
        200: OpenApiResponse(description="List of songs or deletion confirmation"),
        400: OpenApiResponse(description="Invalid device ID or device not found"),
        404: OpenApiResponse(description="Device or Song Not found"),
        500: OpenApiResponse(description="Internal server error"),
        403: OpenApiResponse(
            description="Forbidden – no active session or invalid access code",
            examples=[ OpenApiExample(name="Forbidden", value={"error": "Invalid Access-Code header."}) ]
        ),
    },
    methods=["GET", "DELETE"],
    tags=["LAN Song Manager"]
)
@api_view(["GET", "DELETE"])
def list_delete_device_songs_view(request, device_id: str):
    try:
        SongManager.verify_access(request.headers.get("Access-Code"))
        if request.method == "GET":
            songs = SongManager.list_songs(str(device_id))
            return Response(songs, status=status.HTTP_200_OK)
        elif request.method == "DELETE":
            result = SongManager.delete_all_songs(str(id))
            return Response(result, status=status.HTTP_200_OK)
    except PermissionDenied as e:
        return Response({"error": str(e)}, status=403)
    except ValidationError as e:
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@extend_schema(
    summary="Add Single Song Metadata",
    description="Adds metadata for one song under a specific device.",
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "artist": {"type": "string"},
                "duration_seconds": {"type": "integer"},
                "file_size_kb": {"type": "integer"},
                "file_format": {"type": "string"}
            },
            "required": ["title", "duration_seconds", "file_size_kb", "file_format"]
        }
    },
    responses={
        200: OpenApiResponse(description="Song added", examples=[
            OpenApiExample(name="Success", value={"song_id": "...", "message": "Song added successfully."})
        ]),
        400: OpenApiResponse(description="Validation error"),
        404: OpenApiResponse(description="Device or Song Not found"),
        500: OpenApiResponse(description="Internal server error"),
        403: OpenApiResponse(
            description="Forbidden – no active session or invalid access code",
            examples=[ OpenApiExample(name="Forbidden", value={"error": "Invalid Access-Code header."}) ]
        ),
    },
    methods=["POST"],
    tags=["LAN Song Manager"]
)
@api_view(["POST"])
def add_single_song_metadata(request, device_id):
    try:
        SongManager.verify_access(request.headers.get("Access-Code"))
        result = SongManager.add_song(str(device_id), request.data)
        return Response(result, status=200)
    except PermissionDenied as e:
        return Response({"error": str(e)}, status=403)
    except ValidationError as e:
        return Response({"error": str(e)}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)





@extend_schema(
    summary="Update or Delete Song",
    description="Updates metadata or deletes a specific song belonging to a device.",
    request=SongProfileSerializer,  # Used only for PATCH
    responses={
        200: OpenApiResponse(description="Success", examples=[
            OpenApiExample(name="Update Success", value={"message": "Song updated successfully."}),
            OpenApiExample(name="Delete Success", value={"message": "Song deleted successfully."}),
        ]),
        400: OpenApiResponse(description="Bad request"),
        404: OpenApiResponse(description="Device or Song Not found"),
        500: OpenApiResponse(description="Internal server error"),
        403: OpenApiResponse(
            description="Forbidden – no active session or invalid access code",
            examples=[ OpenApiExample(name="Forbidden", value={"error": "Invalid Access-Code header."}) ]
        ),
    },
    methods=["PATCH", "DELETE"],
    tags=["LAN Song Manager"],
)
@api_view(["PATCH", "DELETE"])
def patch_delete_song_view(request, device_id: str, song_id: str):
    try:
        SongManager.verify_access(request.headers.get("Access-Code"))
        if request.method == "PATCH":
            result = SongManager.update_song(str(device_id), str(song_id), request.data)
            return Response(result, status=status.HTTP_200_OK)

        elif request.method == "DELETE":
            result = SongManager.delete_song(str(device_id), str(song_id))
            return Response(result, status=status.HTTP_200_OK)

    except PermissionDenied as e:
        return Response({"error": str(e)}, status=403)
    except ValidationError as e:
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




@extend_schema(
    summary="Upload Song File",
    description="Uploads a song file for a registered song belonging to a specific device.",
    request=SongUploadSerializer,
    responses={
        201: OpenApiResponse(description="Song uploaded", examples=[
            OpenApiExample(name="Success", value={"message": "Song uploaded successfully."})
        ]),
        400: OpenApiResponse(description="Bad request"),
        404: OpenApiResponse(description="Song not found"),
        403: OpenApiResponse(
            description="Forbidden – no active session or invalid access code",
            examples=[ OpenApiExample(name="Forbidden", value={"error": "Invalid Access-Code header."}) ]
        ),
        500: OpenApiResponse(description="Internal server error"),
    },
    methods=["POST"],
    tags=["LAN Song Manager"],
)
@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def upload_song_file_view(request, device_id: str, song_id: str):
    serializer = SongUploadSerializer(data=request.data)
    if serializer.is_valid():
        try:
            SongManager.verify_access(request.headers.get("Access-Code"))
            file = serializer.validated_data["file"]
            result = SongManager.upload_song_file(str(device_id), str(song_id), file)
            return Response(result, status=status.HTTP_201_CREATED)
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=403)
        except ValidationError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@extend_schema(
    summary="Bulk Add Songs",
    description="Allows a device to register multiple songs' metadata at once.",
    request=SongProfileSerializer(many=True),
    responses={
        201: OpenApiResponse(description="Songs added", examples=[
            OpenApiExample(name="Success", value={"added": 5})
        ]),
        400: OpenApiResponse(description="Bad request"),
        404: OpenApiResponse(description="Device not found"),
        403: OpenApiResponse(
            description="Forbidden – no active session or invalid access code",
            examples=[ OpenApiExample(name="Forbidden", value={"error": "Invalid Access-Code header."}) ]
        ),
    },
    methods=["POST"],
    tags=["LAN Song Manager"]
)
@api_view(["POST"])
def bulk_add_songs_view(request, device_id: str):
    serializer = SongProfileSerializer(data=request.data, many=True)
    if serializer.is_valid():
        try:
            SongManager.verify_access(request.headers.get("Access-Code"))
            result = SongManager.bulk_add_songs(str(device_id), serializer.validated_data)
            return Response(result, status=status.HTTP_201_CREATED)
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=403)
        except ValidationError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





@extend_schema(
    summary="Get All Songs from Active Devices",
    description="Returns a list of all songs registered by devices currently active in the LAN session. Requires 'Access-Code' in headers.",
    parameters=[
        OpenApiParameter(
            name="Access-Code",
            type=str,
            location=OpenApiParameter.HEADER,
            required=True,
            description="Access code to authenticate this request"
        )
    ],
    responses={
        200: OpenApiResponse(description="List of songs"),
        403: OpenApiResponse(description="Invalid or missing access code"),
        500: OpenApiResponse(description="Internal server error")
    },
    tags=["LAN Song Manager"]
)
@api_view(["GET"])
@ratelimit(key="ip", rate="10/m", block=True)
def all_songs_from_active_devices_view(request):
    try:
        SongManager.verify_access(request.headers.get("Access-Code"))
        results = SongManager().get_all_songs_from_active_devices()
        return Response(results, status=200)
    except PermissionError as e:
        return Response({"error": str(e)}, status=403)
    except Exception as e:
        return Response({"error": str(e)}, status=500)
