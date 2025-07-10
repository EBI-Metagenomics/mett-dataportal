from django.conf import settings
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include

from dataportal.router import api

admin.site.site_header = "ME TT Data Portal Admin"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    path("", include("django_prometheus.urls")),
]

if settings.DEBUG:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]

def custom_404(request, exception):
    # Only return JSON for API routes
    if request.path.startswith("/api/"):
        return JsonResponse({
            "status": "error",
            "message": "Not found",
            "error_code": "NOT_FOUND",
            "request_id": None
        }, status=404)
    # Otherwise, fall back to default HTML
    from django.views.defaults import page_not_found
    return page_not_found(request, exception)

handler404 = custom_404