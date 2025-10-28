import logging
from typing import Optional

from ninja import Router, Query, Path

from dataportal.api.core.gene_endpoints import gene_router
from dataportal.authentication import APIRoles, RoleBasedJWTAuth
from dataportal.schema.experimental.fitness_schemas import FitnessSearchQuerySchema
from dataportal.schema.response_schemas import SuccessResponseSchema, create_success_response
from dataportal.services.experimental.fitness_data_service import FitnessDataService
from dataportal.utils.errors import raise_not_found_error, raise_internal_server_error, raise_validation_error
from dataportal.utils.exceptions import GeneNotFoundError, ServiceError
from dataportal.utils.response_wrappers import wrap_success_response
from dataportal.utils.utils import split_comma_param

logger = logging.getLogger(__name__)

fitness_service = FitnessDataService()

ROUTER_FITNESS = "Fitness"
fitness_router = Router(tags=[ROUTER_FITNESS])


@gene_router.get(
    "/{locus_tag}/fitness",
    response=SuccessResponseSchema,
    summary="Get fitness data for a gene",
    description=(
        "Retrieves fitness data for a specific gene using its locus tag or UniProt ID. "
        "Returns basic gene information along with fitness data including log fold change, "
        "FDR, and experimental conditions."
    ),
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.FITNESS]),
    include_in_schema=False,
)
@wrap_success_response
async def get_fitness_by_gene(
    request,
    locus_tag: str = Path(..., description="Gene locus tag or UniProt ID"),
):
    """Get fitness data for a specific gene."""
    try:
        result = await fitness_service.get_by_id(locus_tag)
        
        if not result.fitness or len(result.fitness) == 0:
            return create_success_response(
                data=result,
                message=f"No fitness data found for gene {locus_tag}"
            )
        
        return create_success_response(
            data=result,
            message=f"Fitness data for gene {locus_tag} retrieved successfully"
        )
    except GeneNotFoundError as e:
        logger.error(f"Gene not found: {locus_tag}")
        raise_not_found_error(
            f"Gene with identifier '{locus_tag}' not found",
            error_code="GENE_NOT_FOUND"
        )
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise_internal_server_error(f"Failed to fetch fitness data for '{locus_tag}'")


@fitness_router.get(
    "/search",
    response=SuccessResponseSchema,
    summary="Search fitness data with filters",
    description=(
        "Search for fitness data across genes with optional filters. "
        "Supports identifier-based search and discovery mode (filter-only queries)."
    ),
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.FITNESS]),
    include_in_schema=False,
)
@wrap_success_response
async def search_fitness(
    request,
    query: FitnessSearchQuerySchema = Query(...),
):
    """Search for fitness data by identifiers and/or filters."""
    try:
        locus_tags = split_comma_param(query.locus_tags) if query.locus_tags else []
        uniprot_ids = split_comma_param(query.uniprot_ids) if query.uniprot_ids else []
        
        has_identifiers = locus_tags or uniprot_ids
        has_filters = any([
            query.contrast,
            query.min_lfc,
            query.max_fdr,
            query.min_barcodes
        ])
        
        if not has_identifiers and not has_filters:
            raise_validation_error(
                "At least one search criterion must be provided: "
                "locus_tags, uniprot_ids, or filter parameters"
            )
        
        total_identifiers = len(locus_tags) + len(uniprot_ids)
        if total_identifiers > 1000:
            raise_validation_error("Maximum 1000 total identifiers allowed per search request")
        
        results = await fitness_service.search_with_filters(
            locus_tags=locus_tags,
            uniprot_ids=uniprot_ids,
            contrast=query.contrast,
            min_lfc=query.min_lfc,
            max_fdr=query.max_fdr,
            min_barcodes=query.min_barcodes,
        )
        
        return create_success_response(
            data=results,
            message=f"Found {len(results)} genes with fitness data"
        )
    except ServiceError as e:
        logger.error(f"Service error in fitness search: {e}")
        raise_internal_server_error(f"Failed to search fitness data: {str(e)}")

