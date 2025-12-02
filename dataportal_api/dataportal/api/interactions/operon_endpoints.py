"""
API endpoints for operon queries.

This module provides REST API endpoints for querying operon information,
finding operons containing specific genes, and analyzing operon composition.
"""

import logging
from typing import Optional
from ninja import Router, Query
from ninja.errors import HttpError

from dataportal.api.core import gene_router
from dataportal.authentication import APIRoles, RoleBasedJWTAuth
from dataportal.services.interactions.operon_service import OperonService
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

ROUTER_OPERONS = "Operons"
operon_router = Router(tags=[ROUTER_OPERONS])

# Initialize service
operon_service = OperonService()


# ---- API Endpoints ----


@gene_router.get(
    "/{locus_tag}/operons",
    response=SuccessResponseSchema,
    summary="Get operons containing a gene",
    description="Get all operons that contain a specific gene",
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.OPERONS]),
)
@wrap_success_response
async def get_gene_operons(
    request,
    locus_tag: str,
    species_acronym: Optional[str] = Query(None, description="Filter by species"),
):
    """Get all operons containing a specific gene."""
    try:
        operons = await operon_service.get_operons_by_gene(
            locus_tag=locus_tag, species_acronym=species_acronym
        )

        return create_success_response(
            data=operons, message=f"Found {len(operons)} operons containing gene {locus_tag}"
        )
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise_internal_server_error(f"Failed to get operons: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise_internal_server_error("Internal server error")


@operon_router.get(
    "/search",
    response=PaginatedResponseSchema,
    summary="Search operons with filters",
    description="Search for operons with various filters and pagination",
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.OPERONS]),
)
@wrap_paginated_response
async def search_operons(
    request,
    locus_tag: Optional[str] = Query(
        None, description="Filter by gene (operons containing this gene)"
    ),
    operon_id: Optional[str] = Query(None, description="Filter by operon ID"),
    species_acronym: Optional[str] = Query(None, description="Filter by species"),
    isolate_name: Optional[str] = Query(None, description="Filter by isolate"),
    has_tss: Optional[bool] = Query(None, description="Filter by presence of TSS"),
    has_terminator: Optional[bool] = Query(None, description="Filter by presence of terminator"),
    min_gene_count: Optional[int] = Query(None, ge=2, description="Minimum number of genes"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=10000, description="Results per page"),
):
    """Search operons with filters."""
    try:
        results = await operon_service.search_operons(
            locus_tag=locus_tag,
            operon_id=operon_id,
            species_acronym=species_acronym,
            isolate_name=isolate_name,
            has_tss=has_tss,
            has_terminator=has_terminator,
            min_gene_count=min_gene_count,
            page=page,
            per_page=per_page,
        )

        return results
    except ServiceError as e:
        logger.error(f"Service error in operon search: {e}")
        raise_internal_server_error(f"Failed to search operons: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise_internal_server_error("Internal server error")


@operon_router.get(
    "/statistics",
    response=SuccessResponseSchema,
    summary="Get operon statistics",
    description="Get statistics about operons in the dataset",
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.OPERONS]),
    include_in_schema=False,
)
@wrap_success_response
async def get_operon_statistics(
    request,
    species_acronym: Optional[str] = Query(None, description="Filter by species"),
):
    """Get statistics about operons."""
    try:
        stats = await operon_service.get_operon_statistics(species_acronym=species_acronym)

        return create_success_response(
            data=stats, message="Operon statistics retrieved successfully"
        )
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise_internal_server_error(f"Failed to get statistics: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise_internal_server_error("Internal server error")


@operon_router.get(
    "/{operon_id}",
    response=SuccessResponseSchema,
    summary="Get operon by ID",
    description="Get detailed information about a specific operon",
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.OPERONS]),
)
@wrap_success_response
async def get_operon_by_id(
    request,
    operon_id: str,
):
    """Get operon by ID."""
    try:
        operon = await operon_service.get_by_id(operon_id)

        if operon is None:
            raise_not_found_error(
                message=f"Operon {operon_id} not found",
                error_code=ErrorCode.OPERON_NOT_FOUND,
            )

        return create_success_response(
            data=operon, message=f"Operon {operon_id} retrieved successfully"
        )
    except HttpError:
        raise
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise_internal_server_error(f"Failed to get operon: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise_internal_server_error("Internal server error")
