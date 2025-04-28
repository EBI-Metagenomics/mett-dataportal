from django.conf import settings
from django.contrib import admin
from django.urls import path, include

from dataportal.api import api

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
