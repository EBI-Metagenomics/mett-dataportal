"""
WSGI config for ME TT DataPortal project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
"""

import os

from asgiref.sync import async_to_sync
from django.core.wsgi import get_wsgi_application

from dataportal.services.gene_service import GeneService

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dataportal.settings")

# Load essentiality data into cache AFTER the application is initialized
gene_service = GeneService()
async_to_sync(gene_service.load_essentiality_data_by_strain)()

application = get_wsgi_application()
