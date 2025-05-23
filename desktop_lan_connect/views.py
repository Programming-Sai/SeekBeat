import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample
from .lan_utils.initialization import LANCreator
from django_ratelimit.decorators import ratelimit


logger = logging.getLogger('seekbeat')
handler = logging.getLogger('seekbeat').handlers[0]
handler.doRollover()


lan = LANCreator()



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
    tags=["LAN Session"]
)
@api_view(["GET"])
def start_lan_session_view(request):
    allow_override = request.GET.get("override", "false").lower() == "true"

    try:
        qr_path, _ = lan.initialize_session(allow_override=allow_override)
        return Response({"qr_path": qr_path})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)





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
    tags=["LAN Session"]
)
@api_view(["GET"])
@ratelimit(key='ip', rate='10/m', block=True)
def check_lan_session_status(request):
    try:
        isActive = lan.has_active_session()
        session_data = lan.get_session_data()
        if isActive:
            return Response({"active": True, "access_code": session_data.get("access_code")})
        return Response({"active": False})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@extend_schema(
    summary="Terminate LAN Session",
    description="Terminates the currently active LAN session and removes the QR code.",
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
    tags=["LAN Session"]
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
