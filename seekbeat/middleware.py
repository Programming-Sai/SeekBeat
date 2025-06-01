# middleware.py
from django.http import HttpResponseForbidden
from desktop_lan_connect.models import DeviceProfile


class RestrictByIPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = request.META.get('REMOTE_ADDR')

        try:
            allowed_ips = [d.ip_address for d in DeviceProfile.objects.all()]
        except Exception:
            # DB not ready or error, allow access during startup
            return self.get_response(request)

        if ip not in allowed_ips:
            return HttpResponseForbidden("Your device is not authorized.")
        return self.get_response(request)
