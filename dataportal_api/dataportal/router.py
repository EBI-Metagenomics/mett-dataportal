import logging

from django.http import JsonResponse
from ninja import NinjaAPI
from ninja.errors import HttpError

from dataportal.api.gene_endpoints import gene_router
from dataportal.api.genome_endpoints import genome_router
from dataportal.api.health_endpoints import health_router
from dataportal.api.metadata_endpoints import metadata_router
from dataportal.api.species_endpoints import species_router
from pyhmmer_search.api import pyhmmer_router

logger = logging.getLogger(__name__)

api = NinjaAPI(
    title="ME TT DataPortal Data Portal API",
    description="ME TT DataPortal Data Portal APIs to fetch Gut Microbes Genomes / Genes information.",
    urls_namespace="api",
    csrf=False,
    docs_url="/docs",
)

URL_PREFIX_SPECIES = "/species"
URL_PREFIX_GENOMES = "/genomes"
URL_PREFIX_GENES = "/genes"
URL_PREFIX_METADATA = "/metadata"
URL_PREFIX_PYHMMER = "/pyhmmer"


def custom_error_handler(request, exc):
    if isinstance(exc, HttpError):
        return JsonResponse({"error": str(exc)}, status=exc.status_code)
    return JsonResponse({"error": "Internal server error"}, status=500)


# Register routers with the main API
api.add_router(URL_PREFIX_SPECIES, species_router)
api.add_router(URL_PREFIX_GENOMES, genome_router)
api.add_router(URL_PREFIX_GENES, gene_router)
api.add_router(URL_PREFIX_METADATA, metadata_router)
api.add_router(URL_PREFIX_PYHMMER, pyhmmer_router)
api.add_router("/", health_router)
api.add_exception_handler(Exception, custom_error_handler)
