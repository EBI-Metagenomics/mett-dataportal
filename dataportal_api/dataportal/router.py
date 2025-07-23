import logging
import uuid
import json
from django.http import JsonResponse
from ninja import NinjaAPI
from ninja.errors import HttpError

from dataportal.api.gene_endpoints import gene_router
from dataportal.api.genome_endpoints import genome_router
from dataportal.api.health_endpoints import health_router
from dataportal.api.metadata_endpoints import metadata_router
from dataportal.api.species_endpoints import species_router
from dataportal.api.feedback_endpoints import feedback_router

from pyhmmer_search.results.api import pyhmmer_router_result
from pyhmmer_search.search.api import pyhmmer_router_search
from django.conf import settings

from dataportal.schema.response_schemas import (
    ErrorCode,
    create_error_response,
)
from dataportal.utils.exceptions import (
    ServiceError,
    ValidationError,
    GeneNotFoundError,
    GenomeNotFoundError,
    InvalidGenomeIdError,
    SpeciesNotFoundError,
    ElasticsearchError,
    DatabaseError,
    RateLimitError,
    AuthenticationError,
    AuthorizationError,
)

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
URL_PREFIX_PYHMMER_SEARCH = "/pyhmmer/search"
URL_PREFIX_PYHMMER_RESULT = "/pyhmmer/result"
URL_PREFIX_FEEDBACK = "/feedback"


def custom_error_handler(request, exc):
    """Enhanced error handler with standardized response format."""

    request_id = str(uuid.uuid4())

    # Handle HttpError (already formatted)
    if isinstance(exc, HttpError):
        logger.error(
            f"HttpError received: type={type(exc.message)}, message={exc.message}"
        )
        # If the error is a dict, return as is
        if isinstance(exc.message, dict):
            return JsonResponse(exc.message, status=exc.status_code)
        # If the error is a string, try to parse as JSON
        try:
            data = json.loads(exc.message)
            logger.error(f"Successfully parsed JSON: {data}")
            return JsonResponse(data, status=exc.status_code)
        except Exception as e:
            # Log the parsing error for debugging
            logger.error(
                f"Failed to parse HttpError message as JSON: {exc.message}, error: {e}"
            )
            return JsonResponse({"detail": exc.message}, status=exc.status_code)

    # Handle custom exceptions
    if isinstance(exc, GeneNotFoundError):
        error_response = create_error_response(
            error_code=ErrorCode.GENE_NOT_FOUND, message=str(exc), request_id=request_id
        )
        return JsonResponse(error_response.model_dump(), status=404)

    elif isinstance(exc, GenomeNotFoundError):
        error_response = create_error_response(
            error_code=ErrorCode.GENOME_NOT_FOUND,
            message=str(exc),
            request_id=request_id,
        )
        return JsonResponse(error_response.model_dump(), status=404)

    elif isinstance(exc, SpeciesNotFoundError):
        error_response = create_error_response(
            error_code=ErrorCode.SPECIES_NOT_FOUND,
            message=str(exc),
            request_id=request_id,
        )
        return JsonResponse(error_response.model_dump(), status=404)

    elif isinstance(exc, InvalidGenomeIdError):
        error_response = create_error_response(
            error_code=ErrorCode.INVALID_GENOME_ID,
            message=str(exc),
            request_id=request_id,
        )
        return JsonResponse(error_response.model_dump(), status=400)

    elif isinstance(exc, ValidationError):
        error_response = create_error_response(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=str(exc),
            request_id=request_id,
        )
        return JsonResponse(error_response.model_dump(), status=400)

    elif isinstance(exc, ElasticsearchError):
        error_response = create_error_response(
            error_code=ErrorCode.ELASTICSEARCH_ERROR,
            message=str(exc),
            request_id=request_id,
        )
        return JsonResponse(error_response.model_dump(), status=500)

    elif isinstance(exc, DatabaseError):
        error_response = create_error_response(
            error_code=ErrorCode.DATABASE_ERROR, message=str(exc), request_id=request_id
        )
        return JsonResponse(error_response.model_dump(), status=500)

    elif isinstance(exc, RateLimitError):
        error_response = create_error_response(
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=str(exc),
            request_id=request_id,
        )
        return JsonResponse(error_response.model_dump(), status=429)

    elif isinstance(exc, AuthenticationError):
        error_response = create_error_response(
            error_code=ErrorCode.UNAUTHORIZED, message=str(exc), request_id=request_id
        )
        return JsonResponse(error_response.model_dump(), status=401)

    elif isinstance(exc, AuthorizationError):
        error_response = create_error_response(
            error_code=ErrorCode.FORBIDDEN, message=str(exc), request_id=request_id
        )
        return JsonResponse(error_response.model_dump(), status=403)

    elif isinstance(exc, ServiceError):
        error_response = create_error_response(
            error_code=getattr(exc, "error_code", ErrorCode.INTERNAL_SERVER_ERROR),
            message=str(exc),
            request_id=request_id,
        )
        return JsonResponse(error_response.model_dump(), status=500)

    # Handle generic exceptions
    else:
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        error_response = create_error_response(
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            message="An unexpected error occurred",
            request_id=request_id,
        )
        return JsonResponse(error_response.model_dump(), status=500)


def _map_exception_to_error_code(exc: Exception) -> ErrorCode:
    """Map exception types to error codes."""
    if hasattr(exc, "error_code"):
        return exc.error_code

    # Default mapping based on exception type
    if isinstance(exc, (GeneNotFoundError, GenomeNotFoundError, SpeciesNotFoundError)):
        return ErrorCode.GENE_NOT_FOUND
    elif isinstance(exc, InvalidGenomeIdError):
        return ErrorCode.INVALID_GENOME_ID
    elif isinstance(exc, ValidationError):
        return ErrorCode.VALIDATION_ERROR
    elif isinstance(exc, ElasticsearchError):
        return ErrorCode.ELASTICSEARCH_ERROR
    elif isinstance(exc, DatabaseError):
        return ErrorCode.DATABASE_ERROR
    elif isinstance(exc, RateLimitError):
        return ErrorCode.RATE_LIMIT_EXCEEDED
    elif isinstance(exc, AuthenticationError):
        return ErrorCode.UNAUTHORIZED
    elif isinstance(exc, AuthorizationError):
        return ErrorCode.FORBIDDEN
    else:
        return ErrorCode.INTERNAL_SERVER_ERROR


# Register routers with the main API
api.add_router(URL_PREFIX_SPECIES, species_router)
api.add_router(URL_PREFIX_GENOMES, genome_router)
api.add_router(URL_PREFIX_GENES, gene_router)
api.add_router(URL_PREFIX_METADATA, metadata_router)

if getattr(settings, "ENABLE_PYHMMER_SEARCH", False):
    api.add_router(URL_PREFIX_PYHMMER_SEARCH, pyhmmer_router_search)
    api.add_router(URL_PREFIX_PYHMMER_RESULT, pyhmmer_router_result)

# Conditionally register feedback router based on feature flag
if getattr(settings, "ENABLE_FEEDBACK", False):
    api.add_router(URL_PREFIX_FEEDBACK, feedback_router)

api.add_router("/", health_router)
# Register specific handlers
api.add_exception_handler(HttpError, custom_error_handler)
api.add_exception_handler(Exception, custom_error_handler)
