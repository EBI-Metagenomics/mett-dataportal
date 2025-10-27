"""
API endpoints for gene fitness correlation queries.

This module provides REST API endpoints for querying gene-gene fitness
correlations, finding correlated genes, and analyzing correlation networks.
"""

import logging
from typing import Optional
from ninja import Router, Query
from ninja.errors import HttpError

from dataportal.api.core import gene_router
from dataportal.authentication import RoleBasedJWTAuth, APIRoles
from dataportal.services.interactions.fitness_correlation_service import FitnessCorrelationService
from dataportal.schema.interactions.fitness_correlation_schemas import (
    GeneCorrelationQuerySchema,
    GenePairCorrelationQuerySchema,
    TopCorrelationsQuerySchema,
    CorrelationSearchQuerySchema,
)
from dataportal.schema.response_schemas import create_success_response
from dataportal.utils.exceptions import ServiceError
from dataportal.utils.response_wrappers import wrap_success_response

logger = logging.getLogger(__name__)

ROUTER_FITNESS_CORRELATION = "Gene Fitness Correlations"
fitness_correlation_router = Router(tags=[ROUTER_FITNESS_CORRELATION])

# Initialize service
fitness_correlation_service = FitnessCorrelationService()


# ---- API Endpoints ----

@gene_router.get(
    "/{locus_tag}/correlations",
    summary="Get correlations for a gene",
    description="Get all genes correlated with a specific gene, ordered by correlation strength",
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.FITNESS_CORRELATION]),
)
@wrap_success_response
async def get_gene_correlations(
    request,
    locus_tag: str,
    species_acronym: Optional[str] = Query(None),
    min_correlation: Optional[float] = Query(None, description="Minimum absolute correlation value"),
    max_results: int = Query(100, description="Maximum number of results to return")
):
    """Get all correlations for a specific gene."""
    try:
        correlations = await fitness_correlation_service.get_correlations_for_gene(
            locus_tag=locus_tag,
            species_acronym=species_acronym,
            min_correlation=min_correlation,
            max_results=max_results
        )

        return create_success_response(
            data={"correlations": correlations, "locus_tag": locus_tag, "count": len(correlations)},
            message=f"Found {len(correlations)} correlations for gene {locus_tag}"
        )
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise HttpError(500, f"Failed to get correlations: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HttpError(500, "Internal server error")


@fitness_correlation_router.get(
    "/correlation",
    summary="Get correlation between two genes",
    description="Get the correlation value between two specific genes",
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.FITNESS_CORRELATION]),
)
@wrap_success_response
async def get_gene_pair_correlation(
    request,
    locus_tag_a: str = Query(..., description="First gene locus tag"),
    locus_tag_b: str = Query(..., description="Second gene locus tag"),
    species_acronym: Optional[str] = Query(None)
):
    """Get correlation between two specific genes."""
    try:
        correlation = await fitness_correlation_service.get_correlation_between_genes(
            locus_tag_a=locus_tag_a,
            locus_tag_b=locus_tag_b,
            species_acronym=species_acronym
        )

        if correlation is None:
            raise HttpError(404, f"No correlation found between {locus_tag_a} and {locus_tag_b}")

        return create_success_response(
            data=correlation,
            message=f"Correlation between {locus_tag_a} and {locus_tag_b} retrieved successfully"
        )
    except HttpError:
        raise
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise HttpError(500, f"Failed to get correlation: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HttpError(500, "Internal server error")


@fitness_correlation_router.get(
    "/top",
    summary="Get top correlations",
    description="Get the strongest correlations in the dataset",
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.FITNESS_CORRELATION]),
    include_in_schema=False,
)
@wrap_success_response
async def get_top_correlations(
    request,
    species_acronym: Optional[str] = Query(None),
    correlation_strength: Optional[str] = Query(
        None,
        description="Filter by strength (e.g., strong_positive, strong_negative, moderate_positive)"
    ),
    limit: int = Query(100, description="Number of results to return")
):
    """Get top correlations across the dataset."""
    try:
        correlations = await fitness_correlation_service.get_top_correlations(
            species_acronym=species_acronym,
            correlation_strength=correlation_strength,
            limit=limit
        )

        return create_success_response(
            data={"correlations": correlations, "count": len(correlations)},
            message=f"Retrieved top {len(correlations)} correlations"
        )
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise HttpError(500, f"Failed to get top correlations: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HttpError(500, "Internal server error")


@fitness_correlation_router.get(
    "/statistics",
    summary="Get correlation statistics",
    description="Get statistics about correlations in the dataset",
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.FITNESS_CORRELATION]),
    include_in_schema=False,
)
@wrap_success_response
async def get_correlation_statistics(
    request,
    species_acronym: Optional[str] = Query(None)
):
    """Get statistics about correlations."""
    try:
        stats = await fitness_correlation_service.get_correlation_statistics(
            species_acronym=species_acronym
        )

        return create_success_response(
            data=stats,
            message="Correlation statistics retrieved successfully"
        )
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise HttpError(500, f"Failed to get statistics: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HttpError(500, "Internal server error")


@fitness_correlation_router.get(
    "/search",
    summary="Search correlations",
    description="Search correlations by gene name or product description",
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.FITNESS_CORRELATION]),
)
@wrap_success_response
async def search_correlations(
    request,
    query: str = Query(..., description="Search query (gene name or product)"),
    species_acronym: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """Search correlations by gene name or product."""
    try:
        results = await fitness_correlation_service.search_correlations(
            query=query,
            species_acronym=species_acronym,
            page=page,
            per_page=per_page
        )

        return create_success_response(
            data=results,
            message=f"Found {results['total']} correlations matching '{query}'"
        )
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise HttpError(500, f"Failed to search correlations: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HttpError(500, "Internal server error")


@fitness_correlation_router.get(
    "/strength-categories",
    summary="Get available correlation strength categories",
    description="Get list of available correlation strength categories for filtering",
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.FITNESS_CORRELATION]),
    include_in_schema=False,
)
@wrap_success_response
async def get_correlation_strengths(request):
    """Get available correlation strength categories."""
    try:
        categories = [
            "strong_positive",
            "moderate_positive",
            "weak",
            "moderate_negative",
            "strong_negative"
        ]

        return create_success_response(
            data={"strength_categories": categories},
            message="Correlation strength categories retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HttpError(500, "Internal server error")

