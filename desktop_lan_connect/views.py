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
    description=(
        "Generates a QR code to join a local LAN session. "
        "Supports optional override to terminate existing session. "
        "Customize QR fill and background colors using named colors or hex codes (e.g., '#222222')."
    ),
    parameters=[
        OpenApiParameter(
            name="override",
            description="Whether to terminate and recreate an existing session (true/false).",
            required=False,
            type=bool,
            location=OpenApiParameter.QUERY
        ),
        OpenApiParameter(
            name="fill",
            description="Color of QR code modules (default 'black'). Supports named colors or hex codes.",
            required=False,
            type=str,
            location=OpenApiParameter.QUERY
        ),
        OpenApiParameter(
            name="back",
            description="Background color of QR code (default 'white'). Supports named colors or hex codes.",
            required=False,
            type=str,
            location=OpenApiParameter.QUERY
        ),
        OpenApiParameter(
            name="theme",
            description="UI theme preference, e.g., 'dark' or 'light' (default 'dark').",
            required=False,
            type=str,
            location=OpenApiParameter.QUERY
        ),
    ],
    responses={
        200: OpenApiResponse(
            description="QR code path returned",
            examples=[
                OpenApiExample(
                    name="Session Started",
                    summary="Successful response",
                    value={"qr_path": "/path/to/qr_code.png"},
                    response_only=True
                )
            ],
        ),
        400: OpenApiResponse(
            description="Session already exists or error occurred",
            examples=[
                OpenApiExample(
                    name="Session Already Exists",
                    summary="Attempt to start without override",
                    value={"error": "Session already exists. Use override to force new session."},
                    response_only=True
                )
            ],
        ),
    },
    methods=["GET"],
    tags=["LAN Session Manager"],
)
@api_view(["GET"])
def start_lan_session_view(request):
    allow_override = request.GET.get("override", "false").lower() == "true"
    fill_color = request.GET.get("fill", "black")
    back_color = request.GET.get("back", "white")
    theme = request.GET.get("theme", "dark")
    logger.info("Session Started with override=%s, fill=%s, back=%s, theme=%s", allow_override, fill_color, back_color, theme)

    try:
        qr_path, _ = lan.initialize_session(
            allow_override=allow_override,
            fill_color=fill_color,
            back_color=back_color,
            theme=theme,
        )
        logger.info("New LAN session initialized; qr_path=%s", qr_path)
        return Response({"qr_path": qr_path})
    except Exception as e:
        logger.error("Failed to start LAN session: %s", str(e), exc_info=True)
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
    logger.info("Checking Session Status; check call made from %s", request.META.get('REMOTE_ADDR'))
    try:
        isActive = lan.has_active_session()
        if isActive:
            logger.info("LAN session Active")
            return Response({"active": True })
        logger.info("LAN session Inactive")
        return Response({"active": False})
    except Exception as e:
        logger.exception("Error checking LAN session status")
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
    logger.info("Terminate Session Call with; access_code=%s", access_code)
    try:
        isActive = lan.has_active_session()
        session_data = lan.get_session_data()
        if not isActive:
            logger.warning("No active session to terminate")
            return Response({"error": "No active session found."}, status=status.HTTP_400_BAD_REQUEST)

        qr_path = session_data.get("qr_path")
        res = lan.terminate_session(qr_path, access_code)
        logger.info("LAN session terminated; result=%s", res)
        return Response(res, status=200)
    except Exception as e:
        logger.error("Failed to terminate LAN session: %s", str(e), exc_info=True)
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
    logger.info("Device Handshake Initiated; META=%s, data=%s", request.META, request.data)
    try:
        data = request.data
        ip_address = request.META.get('REMOTE_ADDR')
        if not lan.has_active_session(): 
            logger.warning("Handshake denied: no active session")
            return Response( {"error": "No active LAN session. Cannot register device."}, status=status.HTTP_403_FORBIDDEN)
        
        access_code = request.headers.get("Access-Code")
        system_access_code = lan.get_session_data()["access_code"]
        result, status_ = device_manager.handshake(data, access_code, system_access_code, ip_address)
        logger.info("Handshake result=%s status=%s", result, status_)
        return Response(result, status=status_)
    except PermissionDenied as pd:
        logger.warning("Handshake permission denied: %s", pd)
        return Response({"error": str(pd)}, status=status.HTTP_403_FORBIDDEN)
    except Exception as e:
        logger.exception("Error during device handshake")
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
    logger.info("Device Reconnect Requested called; META=%s, data=%s", request.META, request.data)
    try:
        data = request.data
        if not lan.has_active_session():
            logger.warning("Reconnect denied: no active session") 
            return Response( {"error": "No active LAN session. Cannot register device."}, status=status.HTTP_403_FORBIDDEN)
        
        access_code = request.headers.get("Access-Code")
        system_access_code = lan.get_session_data()["access_code"]
        result, status_ = device_manager.reconnect(data, access_code, system_access_code)
        logger.info("Reconnect result=%s status=%s", result, status_)
        return Response(result, status=status_)
    except PermissionDenied as pd:
        logger.warning("Reconnect permission denied: %s", pd)
        return Response({"error": str(pd)}, status=status.HTTP_403_FORBIDDEN)
    except Exception as e:
        logger.exception("Error during device reconnect")
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
    logger.info("Device Disconnect Requested; META=%s, data=%s", request.META, request.data)
    try:
        device_id = request.data.get("device_id")
        keep_data = request.data.get("keep_data", True)
        result, code = device_manager.disconnect(device_id, keep_data)
        SongManager.delete_uploaded_files_for_device(UUID(device_id))
        logger.info("Device %s disconnected; keep_data=%s result=%s", device_id, keep_data, result)
        return Response(result, status=code)
    except PermissionDenied as pd:
        logger.warning("Disconnect permission denied: %s", pd)
        return Response({"error": str(pd)}, status=status.HTTP_403_FORBIDDEN)
    except Exception as e:
        logger.exception("Error during device disconnect")
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
    logger.info("Viewing All active Devices; headers=%s", request.headers)
    try:
        if not lan.has_active_session():
            logger.warning("List devices denied: no active session")
            return Response({"error": "No active LAN session."}, status=status.HTTP_403_FORBIDDEN)
        
        access_code = request.headers.get("Access-Code")
        system_access_code = lan.get_session_data()["access_code"]
        devices_data, status_ = device_manager.get_active_devices(access_code, system_access_code)
        logger.info("Active devices fetched; count=%s", len(devices_data[1]))
        return Response({"count":devices_data[1], "devices": devices_data[0]}, status=status_)
    except PermissionDenied as pd:
        logger.warning("List devices permission denied: %s", pd)
        return Response({"error": str(pd)}, status=status.HTTP_403_FORBIDDEN)
    except Exception as e:
        logger.exception("Error listing active devices")
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
    logger.info("Get/List or Delete all songs; method=%s device_id=%s", request.method, device_id)
    try:
        SongManager.verify_access(request.headers.get("Access-Code"))
        if request.method == "GET":
            songs = SongManager.list_songs(str(device_id))
            logger.info("Fetched %s songs for device %s", len(songs), device_id)
            return Response(songs, status=status.HTTP_200_OK)
        elif request.method == "DELETE":
            result = SongManager.delete_all_songs(str(id))
            logger.info("Deleted all songs for device %s", device_id)
            return Response(result, status=status.HTTP_200_OK)
    except PermissionDenied as pd:
        logger.warning("Access denied in list/delete songs: %s", pd)
        return Response({"error": str(pd)}, status=status.HTTP_403_FORBIDDEN)
    except ValidationError as ve:
        logger.warning("Validation error in list/delete songs: %s", ve)
        return Response({"error": str(ve)}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.exception("Error in list/delete songs for device %s", device_id)
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
    logger.info("Add single song metadata; device_id=%s", device_id)
    try:
        SongManager.verify_access(request.headers.get("Access-Code"))
        result = SongManager.add_song(str(device_id), request.data)
        logger.info("Added song metadata to device %s: %s", device_id, result.get("song_id", "N/A"))
        return Response(result, status=200)
    except PermissionDenied as e:
        logger.warning("Access denied in add_single_song_metadata: %s", e)
        return Response({"error": str(e)}, status=403)
    except ValidationError as e:
        logger.warning("Validation error in add_single_song_metadata: %s", e)
        return Response({"error": str(e)}, status=404)
    except Exception as e:
        logger.exception("Error in add_single_song_metadata for device %s", device_id)
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
    logger.info("Patch or Delete song; method=%s device_id=%s song_id=%s", request.method, device_id, song_id)
    try:
        SongManager.verify_access(request.headers.get("Access-Code"))
        if request.method == "PATCH":
            result = SongManager.update_song(str(device_id), str(song_id), request.data)
            logger.info("Patched song %s for device %s", song_id, device_id)
            return Response(result, status=status.HTTP_200_OK)

        elif request.method == "DELETE":
            result = SongManager.delete_song(str(device_id), str(song_id))
            logger.info("Deleted song %s for device %s", song_id, device_id)
            return Response(result, status=status.HTTP_200_OK)

    except PermissionDenied as pd:
        logger.warning("Access denied for song %s: %s", song_id, pd)
        return Response({"error": str(pd)}, status=status.HTTP_403_FORBIDDEN)
    except ValidationError as ve:
        logger.warning("Validation error for song %s: %s", song_id, ve)
        return Response({"error": str(ve)}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.exception("Error in get/delete for song %s on device %s", song_id, device_id)
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
    logger.info("Upload song; method=%s device_id=%s", request.method, device_id)
    serializer = SongUploadSerializer(data=request.data)
    if serializer.is_valid():
        try:
            SongManager.verify_access(request.headers.get("Access-Code"))
            file = serializer.validated_data["file"]
            result = SongManager.upload_song_file(str(device_id), str(song_id), file)
            logger.info("Uploaded song for device %s", device_id)
            return Response(result, status=status.HTTP_201_CREATED)
        except PermissionDenied as pd:
            logger.warning("Access denied during upload: %s", pd)
            return Response({"error": str(pd)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as ve:
            logger.warning("Validation error during upload: %s", ve)
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception("Upload error for device %s", device_id)
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
    logger.info("Bulk add songs; device_id=%s", device_id)
    serializer = SongProfileSerializer(data=request.data, many=True)
    if serializer.is_valid():
        try:
            SongManager.verify_access(request.headers.get("Access-Code"))
            result = SongManager.bulk_add_songs(str(device_id), serializer.validated_data)
            logger.info("Bulk added %d songs to device %s", len(serializer.validated_data), device_id)
            return Response(result, status=status.HTTP_201_CREATED)
        except PermissionDenied as e:
            logger.warning("Access denied in bulk_add_songs_view: %s", e)
            return Response({"error": str(e)}, status=403)
        except ValidationError as ve:
            logger.warning("Validation error in bulk_add_songs_view: %s", ve)
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception("Error in bulk_add_songs_view for device %s", device_id)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    logger.warning("Serializer validation failed in bulk_add_songs_view: %s", serializer.errors)
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
    logger.info("Fetching all songs from active devices")
    try:
        SongManager.verify_access(request.headers.get("Access-Code"))
        results = SongManager().get_all_songs_from_active_devices()
        logger.info("Fetched %d songs from active devices", len(results))
        return Response(results, status=200)
    except PermissionError as e:
        logger.warning("Access denied in all_songs_from_active_devices_view: %s", e)
        return Response({"error": str(e)}, status=403)
    except Exception as e:
        logger.exception("Error in all_songs_from_active_devices_view")
        return Response({"error": str(e)}, status=500)