from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path, include
from django.views.defaults import page_not_found

from dataportal.api import api

from dataportal.views import (
    HomeView,
)

admin.site.site_header = "ME TT Data Portal Admin"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),

    path("admin/", admin.site.urls),
    path("404/", page_not_found, {"exception": Exception()}),

    # Add the API routes under the /api/ path
    path("api/", api.urls),
]

if settings.DEBUG:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]

urlpatterns += staticfiles_urlpatterns()
