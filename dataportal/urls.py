from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path, include, re_path
from django.views.defaults import page_not_found
from django.views.generic import TemplateView

from dataportal.api import api

from dataportal.views import JBrowseView

admin.site.site_header = "ME TT Data Portal Admin"

urlpatterns = [
    path("jbrowse/<int:isolate_id>/", JBrowseView.as_view(), name="jbrowse_view"),
    path("admin/", admin.site.urls),
    path("404/", page_not_found, {"exception": Exception()}),
    path("api/", api.urls),
    re_path(r"^.*$", TemplateView.as_view(template_name="index.html")),
]

if settings.DEBUG:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]
