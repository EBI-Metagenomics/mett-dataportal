"""
API endpoints for ortholog queries.

This module provides REST API endpoints for querying ortholog relationships
between genes, finding orthologs for specific genes, and analyzing orthology patterns.
"""

import logging
from typing import Optional
from ninja import Router, Query
from ninja.errors import HttpError

from dataportal.api.core import gene_router
from dataportal.authentication import APIRoles, RoleBasedJWTAuth
from dataportal.services.interactions.ortholog_service import OrthologService
from dataportal.schema.response_schemas import (
    SuccessResponseSchema,
    PaginatedResponseSchema,
    create_success_response,
    ErrorCode,
)
from dataportal.utils.errors import (
    raise_not_found_error,
    raise_internal_server_error,
)
from dataportal.utils.exceptions import ServiceError
from dataportal.utils.response_wrappers import wrap_success_response, wrap_paginated_response

logger = logging.getLogger(__name__)

ROUTER_ORTHOLOGS = "Orthologs"
ortholog_router = Router(tags=[ROUTER_ORTHOLOGS])

# Initialize service
ortholog_service = OrthologService()


# ---- API Endpoints ----


@gene_router.get(
    "/{locus_tag}/orthologs",
    response=SuccessResponseSchema,
    summary="Get orthologs for a gene",
    description="Get all orthologous genes for a specific gene across species",
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.ORTHOLOGS]),
    include_in_schema=False,
)
@wrap_success_response
async def get_gene_orthologs(
    request,
    locus_tag: str,
    species_acronym: Optional[str] = Query(None, description="Filter by target species"),
    orthology_type: Optional[str] = Query(
        None, description="Filter by orthology type (1:1, many:1, etc.)"
    ),
    one_to_one_only: bool = Query(False, description="Return only one-to-one orthologs"),
    cross_species_only: bool = Query(False, description="Return only cross-species orthologs"),
    max_results: int = Query(10000, description="Maximum number of results to return", le=100000),
):
    """Get all orthologs for a specific gene."""
    try:
        result = await ortholog_service.get_orthologs_for_gene(
            locus_tag=locus_tag,
            species_acronym=species_acronym,
            orthology_type=orthology_type,
            one_to_one_only=one_to_one_only,
            cross_species_only=cross_species_only,
            max_results=max_results,
        )

        return create_success_response(
            data=result, message=f"Found {result['total_count']} orthologs for gene {locus_tag}"
        )
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise_internal_server_error(f"Failed to get orthologs: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise_internal_server_error("Internal server error")


@ortholog_router.get(
    "/pair",
    response=SuccessResponseSchema,
    summary="Get ortholog relationship between two genes",
    description="Check if two genes are orthologs and get their relationship details",
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.ORTHOLOGS]),
    include_in_schema=False,
)
@wrap_success_response
async def get_ortholog_pair(
    request,
    locus_tag_a: str = Query(..., description="First gene locus tag"),
    locus_tag_b: str = Query(..., description="Second gene locus tag"),
):
    """Get ortholog relationship between two specific genes."""
    try:
        result = await ortholog_service.get_ortholog_pair(
            locus_tag_a=locus_tag_a, locus_tag_b=locus_tag_b
        )

        if result is None:
            raise_not_found_error(
                message=f"No ortholog relationship found between {locus_tag_a} and {locus_tag_b}",
                error_code=ErrorCode.ORTHOLOG_NOT_FOUND,
            )

        return create_success_response(
            data=result,
            message=f"Ortholog relationship between {locus_tag_a} and {locus_tag_b} retrieved successfully",
        )
    except HttpError:
        raise
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise_internal_server_error(f"Failed to get ortholog pair: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise_internal_server_error("Internal server error")


@ortholog_router.get(
    "/search",
    response=PaginatedResponseSchema,
    summary="Search orthologs with filters",
    description="Search for ortholog pairs with various filters and pagination",
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.ORTHOLOGS]),
    include_in_schema=False,
)
@wrap_paginated_response
async def search_orthologs(
    request,
    species_acronym: Optional[str] = Query(None, description="Filter by species"),
    orthology_type: Optional[str] = Query(None, description="Filter by orthology type"),
    one_to_one_only: bool = Query(False, description="Return only one-to-one orthologs"),
    cross_species_only: bool = Query(False, description="Return only cross-species orthologs"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Results per page"),
):
    """Search orthologs with filters."""
    try:
        results = await ortholog_service.search_orthologs(
            species_acronym=species_acronym,
            orthology_type=orthology_type,
            one_to_one_only=one_to_one_only,
            cross_species_only=cross_species_only,
            page=page,
            per_page=per_page,
        )

        return results
    except ServiceError as e:
        logger.error(f"Service error in ortholog search: {e}")
        raise_internal_server_error(f"Failed to search orthologs: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise_internal_server_error("Internal server error")


@ortholog_router.get(
    "/types",
    response=SuccessResponseSchema,
    summary="Get available orthology types",
    description="Get list of available orthology types for filtering",
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.ORTHOLOGS]),
    include_in_schema=False,
)
@wrap_success_response
async def get_orthology_types(request):
    """Get available orthology types."""
    try:
        types = ["1:1", "many:1", "1:many", "many:many"]

        return create_success_response(
            data={"orthology_types": types}, message="Orthology types retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise_internal_server_error("Internal server error")
