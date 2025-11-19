"""
API endpoints for Pooled TTP (Thermal Proteome Profiling) data.
"""

import logging

from ninja import Router, Query, Path

from dataportal.authentication import APIRoles, RoleBasedJWTAuth
from dataportal.schema.response_schemas import (
    SuccessResponseSchema,
    create_success_response,
    PaginatedResponseSchema,
)
from dataportal.schema.interactions.ttp_schemas import (
    TTPInteractionQuerySchema,
    TTPGeneInteractionsQuerySchema,
    TTPCompoundInteractionsQuerySchema,
    TTPHitAnalysisQuerySchema,
    TTPPoolAnalysisQuerySchema,
    TTPDownloadQuerySchema,
)
from dataportal.services.interactions.ttp_service import TTPService
from dataportal.utils.exceptions import ServiceError
from dataportal.utils.errors import (
    raise_validation_error,
    raise_internal_server_error,
)
from dataportal.utils.response_wrappers import wrap_success_response, wrap_paginated_response

logger = logging.getLogger(__name__)

# Initialize service
ttp_service = TTPService()

ROUTER_TTP = "Pooled TTP Interactions"
ttp_router = Router(tags=[ROUTER_TTP])


@ttp_router.get(
    "/metadata",
    response=SuccessResponseSchema,
    summary="Get TTP metadata",
    description="Get metadata about the TTP dataset including counts, available compounds, and score ranges.",
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.TTP]),
    include_in_schema=False,
)
@wrap_success_response
async def get_ttp_metadata(request):
    """Get TTP dataset metadata."""
    try:
        metadata = await ttp_service.get_metadata()
        return create_success_response(metadata)
    except ServiceError as e:
        raise_validation_error(str(e))
    except Exception as e:
        logger.error(f"Error in get_ttp_metadata: {str(e)}")
        raise_internal_server_error("Internal server error")


@ttp_router.get(
    "/search",
    response=PaginatedResponseSchema,
    summary="Search TTP interactions",
    description="Search for protein-compound interactions with basic filtering and pagination.",
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.TTP]),
    include_in_schema=False,
)
@wrap_paginated_response
async def search_interactions(request, query: TTPInteractionQuerySchema = Query(...)):
    """Search TTP interactions with basic query parameters."""
    try:
        return await ttp_service.search_interactions(query)
    except ServiceError as e:
        raise_validation_error(str(e))
    except Exception as e:
        logger.error(f"Error in search_interactions: {str(e)}")
        raise_internal_server_error("Internal server error")


@ttp_router.get(
    "/gene/{locus_tag}/interactions",
    response=SuccessResponseSchema,
    summary="Get gene interactions",
    description="Get all protein-compound interactions for a specific gene.",
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.TTP]),
    include_in_schema=False,
)
@wrap_success_response
async def get_gene_interactions(
    request,
    locus_tag: str = Path(..., description="Locus tag of the gene"),
    query: TTPGeneInteractionsQuerySchema = Query(...),
):
    """Get all interactions for a specific gene."""
    try:
        # Override locus_tag from path parameter
        query.locus_tag = locus_tag
        interactions = await ttp_service.get_gene_interactions(query)
        return create_success_response(interactions)
    except ServiceError as e:
        raise_validation_error(str(e))
    except Exception as e:
        logger.error(f"Error in get_gene_interactions: {str(e)}")
        raise_internal_server_error("Internal server error")


@ttp_router.get(
    "/compound/{compound}/interactions",
    response=SuccessResponseSchema,
    summary="Get compound interactions",
    description="Get all protein-compound interactions for a specific compound.",
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.TTP]),
    include_in_schema=False,
)
@wrap_success_response
async def get_compound_interactions(
    request,
    compound: str = Path(..., description="Name of the compound"),
    query: TTPCompoundInteractionsQuerySchema = Query(...),
):
    """Get all interactions for a specific compound."""
    try:
        # Override compound from path parameter
        query.compound = compound
        interactions = await ttp_service.get_compound_interactions(query)
        return create_success_response(interactions)
    except ServiceError as e:
        raise_validation_error(str(e))
    except Exception as e:
        logger.error(f"Error in get_compound_interactions: {str(e)}")
        raise_internal_server_error("Internal server error")


@ttp_router.get(
    "/hits",
    response=SuccessResponseSchema,
    summary="Hit analysis",
    description="Get significant protein-compound interactions (hits) with summary statistics.",
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.TTP]),
    include_in_schema=False,
)
@wrap_success_response
async def get_hit_analysis(request, query: TTPHitAnalysisQuerySchema = Query(...)):
    """Get hit analysis - significant interactions with summary statistics."""
    try:
        interactions, summary = await ttp_service.get_hit_analysis(query)
        return create_success_response({"genes": interactions, "summary": summary})
    except ServiceError as e:
        raise_validation_error(str(e))
    except Exception as e:
        logger.error(f"Error in get_hit_analysis: {str(e)}")
        raise_internal_server_error("Internal server error")


@ttp_router.get(
    "/pools/analysis",
    response=SuccessResponseSchema,
    summary="Pool analysis",
    description="Get analysis summary for specific experimental pools.",
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.TTP]),
    include_in_schema=False,
)
@wrap_success_response
async def get_pool_analysis(request, query: TTPPoolAnalysisQuerySchema = Query(...)):
    """Get pool-based analysis summary."""
    try:
        summary = await ttp_service.get_pool_analysis(query)
        return create_success_response(summary)
    except ServiceError as e:
        raise_validation_error(str(e))
    except Exception as e:
        logger.error(f"Error in get_pool_analysis: {str(e)}")
        raise_internal_server_error("Internal server error")


@ttp_router.get(
    "/download",
    summary="Download TTP data",
    description="Download TTP interaction data in CSV or TSV format with filtering.",
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.TTP]),
    include_in_schema=False,
)
async def download_ttp_data(request, query: TTPDownloadQuerySchema = Query(...)):
    """Download TTP data in CSV/TSV format."""
    try:
        data = await ttp_service.download_data(query)

        # Set appropriate content type
        content_type = "text/csv" if query.format == "csv" else "text/tab-separated-values"
        filename = f"ttp_interactions.{query.format}"

        from django.http import HttpResponse

        response = HttpResponse(data, content_type=content_type)
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    except ServiceError as e:
        raise_validation_error(str(e))
    except Exception as e:
        logger.error(f"Error in download_ttp_data: {str(e)}")
        raise_internal_server_error("Internal server error")
