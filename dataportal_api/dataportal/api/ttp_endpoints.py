"""
API endpoints for Pooled TTP (Thermal Proteome Profiling) data.
"""

import logging
from typing import List, Tuple
from ninja import Router, Query, Path
from ninja.errors import HttpError

from dataportal.schema.ttp_schemas import (
    TTPInteractionQuerySchema,
    TTPFacetedSearchQuerySchema,
    TTPGeneInteractionsQuerySchema,
    TTPCompoundInteractionsQuerySchema,
    TTPHitAnalysisQuerySchema,
    TTPPoolAnalysisQuerySchema,
    TTPDownloadQuerySchema,
    TTPInteractionSchema,
    TTPInteractionResponseSchema,
    TTPHitSummarySchema,
    TTPPoolSummarySchema,
    TTPMetadataSchema,
    TTPAutocompleteSchema,
    TTPFacetSchema,
)
from dataportal.schema.response_schemas import SuccessResponseSchema, create_success_response, PaginatedResponseSchema
from dataportal.services.ttp_service import TTPService
from dataportal.utils.exceptions import ServiceError
from dataportal.utils.response_wrappers import wrap_success_response, wrap_paginated_response

logger = logging.getLogger(__name__)

# Initialize service
ttp_service = TTPService()

ROUTER_TTP = "Pooled TTP Interactions"
ttp_router = Router(tags=[ROUTER_TTP])


@ttp_router.get(
    "/search",
    response=PaginatedResponseSchema,
    summary="Search TTP interactions",
    description="Search for protein-compound interactions with basic filtering and pagination."
)
@wrap_paginated_response
async def search_interactions(
    request,
    query: TTPInteractionQuerySchema = Query(...)
):
    """Search TTP interactions with basic query parameters."""
    try:
        return await ttp_service.search_interactions(query)
    except ServiceError as e:
        raise HttpError(400, str(e))
    except Exception as e:
        logger.error(f"Error in search_interactions: {str(e)}")
        raise HttpError(500, "Internal server error")


@ttp_router.get(
    "/search/advanced",
    response=TTPInteractionResponseSchema,
    summary="Advanced TTP search",
    description="Advanced search with multiple filters including pools, scores, and hit calling."
)
@wrap_paginated_response
async def advanced_search_interactions(
    request,
    query: TTPFacetedSearchQuerySchema = Query(...)
):
    """Advanced search for TTP interactions with multiple filters."""
    try:
        return await ttp_service.faceted_search(query)
    except ServiceError as e:
        raise HttpError(400, str(e))
    except Exception as e:
        logger.error(f"Error in advanced_search_interactions: {str(e)}")
        raise HttpError(500, "Internal server error")


@ttp_router.get(
    "/gene/{locus_tag}/interactions",
    response=SuccessResponseSchema,
    summary="Get gene interactions",
    description="Get all protein-compound interactions for a specific gene."
)
@wrap_success_response
async def get_gene_interactions(
    request,
    locus_tag: str = Path(..., description="Locus tag of the gene"),
    query: TTPGeneInteractionsQuerySchema = Query(...)
):
    """Get all interactions for a specific gene."""
    try:
        # Override locus_tag from path parameter
        query.locus_tag = locus_tag
        interactions = await ttp_service.get_gene_interactions(query)
        return create_success_response(interactions)
    except ServiceError as e:
        raise HttpError(400, str(e))
    except Exception as e:
        logger.error(f"Error in get_gene_interactions: {str(e)}")
        raise HttpError(500, "Internal server error")


@ttp_router.get(
    "/compound/{compound}/interactions",
    response=SuccessResponseSchema,
    summary="Get compound interactions",
    description="Get all protein-compound interactions for a specific compound."
)
@wrap_success_response
async def get_compound_interactions(
    request,
    compound: str = Path(..., description="Name of the compound"),
    query: TTPCompoundInteractionsQuerySchema = Query(...)
):
    """Get all interactions for a specific compound."""
    try:
        # Override compound from path parameter
        query.compound = compound
        interactions = await ttp_service.get_compound_interactions(query)
        return create_success_response(interactions)
    except ServiceError as e:
        raise HttpError(400, str(e))
    except Exception as e:
        logger.error(f"Error in get_compound_interactions: {str(e)}")
        raise HttpError(500, "Internal server error")


@ttp_router.get(
    "/hits",
    response=SuccessResponseSchema,
    summary="Hit analysis",
    description="Get significant protein-compound interactions (hits) with summary statistics."
)
@wrap_success_response
async def get_hit_analysis(
    request,
    query: TTPHitAnalysisQuerySchema = Query(...)
):
    """Get hit analysis - significant interactions with summary statistics."""
    try:
        interactions, summary = await ttp_service.get_hit_analysis(query)
        return create_success_response({
            "interactions": interactions,
            "summary": summary
        })
    except ServiceError as e:
        raise HttpError(400, str(e))
    except Exception as e:
        logger.error(f"Error in get_hit_analysis: {str(e)}")
        raise HttpError(500, "Internal server error")


@ttp_router.get(
    "/pools/analysis",
    response=SuccessResponseSchema,
    summary="Pool analysis",
    description="Get analysis summary for specific experimental pools."
)
@wrap_success_response
async def get_pool_analysis(
    request,
    query: TTPPoolAnalysisQuerySchema = Query(...)
):
    """Get pool-based analysis summary."""
    try:
        summary = await ttp_service.get_pool_analysis(query)
        return create_success_response(summary)
    except ServiceError as e:
        raise HttpError(400, str(e))
    except Exception as e:
        logger.error(f"Error in get_pool_analysis: {str(e)}")
        raise HttpError(500, "Internal server error")


@ttp_router.get(
    "/metadata",
    response=SuccessResponseSchema,
    summary="Get TTP metadata",
    description="Get metadata about the TTP dataset including counts, available compounds, and score ranges."
)
@wrap_success_response
async def get_ttp_metadata(request):
    """Get TTP dataset metadata."""
    try:
        metadata = await ttp_service.get_metadata()
        return create_success_response(metadata)
    except ServiceError as e:
        raise HttpError(400, str(e))
    except Exception as e:
        logger.error(f"Error in get_ttp_metadata: {str(e)}")
        raise HttpError(500, "Internal server error")


@ttp_router.get(
    "/autocomplete/{field}",
    response=SuccessResponseSchema,
    summary="Autocomplete suggestions",
    description="Get autocomplete suggestions for compounds or genes."
)
@wrap_success_response
async def get_autocomplete_suggestions(
    request,
    field: str = Path(..., description="Field to get suggestions for: 'compound' or 'gene'"),
    query: str = Query(..., description="Query string for autocomplete")
):
    """Get autocomplete suggestions for compounds or genes."""
    try:
        if field not in ["compound", "gene"]:
            raise HttpError(400, "Field must be 'compound' or 'gene'")
        
        suggestions = await ttp_service.autocomplete(query, field)
        return create_success_response(suggestions)
    except ServiceError as e:
        raise HttpError(400, str(e))
    except Exception as e:
        logger.error(f"Error in get_autocomplete_suggestions: {str(e)}")
        raise HttpError(500, "Internal server error")


@ttp_router.get(
    "/download",
    summary="Download TTP data",
    description="Download TTP interaction data in CSV or TSV format with filtering."
)
async def download_ttp_data(
    request,
    query: TTPDownloadQuerySchema = Query(...)
):
    """Download TTP data in CSV/TSV format."""
    try:
        data = await ttp_service.download_data(query)
        
        # Set appropriate content type
        content_type = "text/csv" if query.format == "csv" else "text/tab-separated-values"
        filename = f"ttp_interactions.{query.format}"
        
        from django.http import HttpResponse
        response = HttpResponse(data, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except ServiceError as e:
        raise HttpError(400, str(e))
    except Exception as e:
        logger.error(f"Error in download_ttp_data: {str(e)}")
        raise HttpError(500, "Internal server error")


@ttp_router.get(
    "/compounds",
    response=SuccessResponseSchema,
    summary="List available compounds",
    description="Get list of all available compounds in the TTP dataset."
)
@wrap_success_response
async def get_available_compounds(request):
    """Get list of all available compounds."""
    try:
        metadata = await ttp_service.get_metadata()
        return create_success_response(metadata.available_compounds)
    except ServiceError as e:
        raise HttpError(400, str(e))
    except Exception as e:
        logger.error(f"Error in get_available_compounds: {str(e)}")
        raise HttpError(500, "Internal server error")


@ttp_router.get(
    "/pools",
    response=SuccessResponseSchema,
    summary="List available pools",
    description="Get list of all available experimental pools in the TTP dataset."
)
@wrap_success_response
async def get_available_pools(request):
    """Get list of all available pools."""
    try:
        metadata = await ttp_service.get_metadata()
        return create_success_response(metadata.available_pools)
    except ServiceError as e:
        raise HttpError(400, str(e))
    except Exception as e:
        logger.error(f"Error in get_available_pools: {str(e)}")
        raise HttpError(500, "Internal server error")


@ttp_router.get(
    "/stats/summary",
    response=SuccessResponseSchema,
    summary="Get summary statistics",
    description="Get comprehensive summary statistics for the TTP dataset."
)
@wrap_success_response
async def get_summary_statistics(request):
    """Get comprehensive summary statistics."""
    try:
        metadata = await ttp_service.get_metadata()
        return create_success_response({
            "total_interactions": metadata.total_interactions,
            "total_genes": metadata.total_genes,
            "total_compounds": metadata.total_compounds,
            "total_hits": metadata.total_hits,
            "hit_rate": metadata.hit_rate,
            "score_range": metadata.score_range,
            "available_pools": metadata.available_pools,
            "available_compounds_count": len(metadata.available_compounds)
        })
    except ServiceError as e:
        raise HttpError(400, str(e))
    except Exception as e:
        logger.error(f"Error in get_summary_statistics: {str(e)}")
        raise HttpError(500, "Internal server error")
