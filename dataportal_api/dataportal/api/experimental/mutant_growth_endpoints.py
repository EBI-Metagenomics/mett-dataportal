import logging
from typing import Optional

from ninja import Router, Query, Path

from dataportal.api.core.gene_endpoints import gene_router
from dataportal.schema.experimental.mutant_growth_schemas import MutantGrowthSearchQuerySchema
from dataportal.schema.response_schemas import SuccessResponseSchema, create_success_response
from dataportal.services.experimental.mutant_growth_service import MutantGrowthService
from dataportal.utils.errors import raise_not_found_error, raise_internal_server_error, raise_validation_error
from dataportal.utils.exceptions import GeneNotFoundError, ServiceError
from dataportal.utils.response_wrappers import wrap_success_response
from dataportal.utils.utils import split_comma_param

logger = logging.getLogger(__name__)

mutant_growth_service = MutantGrowthService()

ROUTER_MUTANT_GROWTH = "Mutant Growth"
mutant_growth_router = Router(tags=[ROUTER_MUTANT_GROWTH])


@gene_router.get(
    "/{locus_tag}/mutant-growth",
    response=SuccessResponseSchema,
    summary="Get mutant growth data for a gene",
    description=(
        "Retrieves mutant growth data for a specific gene using its locus tag or UniProt ID. "
        "Returns basic gene information along with mutant growth data including doubling times, "
        "biological replicates, and experimental conditions."
    ),
    include_in_schema=False,
)
@wrap_success_response
async def get_mutant_growth_by_gene(
    request,
    locus_tag: str = Path(..., description="Gene locus tag or UniProt ID"),
):
    """Get mutant growth data for a specific gene."""
    try:
        result = await mutant_growth_service.get_by_id(locus_tag)
        
        if not result.mutant_growth or len(result.mutant_growth) == 0:
            return create_success_response(
                data=result,
                message=f"No mutant growth data found for gene {locus_tag}"
            )
        
        return create_success_response(
            data=result,
            message=f"Mutant growth data for gene {locus_tag} retrieved successfully"
        )
    except GeneNotFoundError as e:
        logger.error(f"Gene not found: {locus_tag}")
        raise_not_found_error(
            f"Gene with identifier '{locus_tag}' not found",
            error_code="GENE_NOT_FOUND"
        )
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise_internal_server_error(f"Failed to fetch mutant growth data for '{locus_tag}'")


@mutant_growth_router.get(
    "/search",
    response=SuccessResponseSchema,
    summary="Search mutant growth data with filters",
    description=(
        "Search for mutant growth data across genes with optional filters. "
        "Supports identifier-based search and discovery mode (filter-only queries)."
    ),
    include_in_schema=False,
)
@wrap_success_response
async def search_mutant_growth(
    request,
    query: MutantGrowthSearchQuerySchema = Query(...),
):
    """Search for mutant growth data by identifiers and/or filters."""
    try:
        locus_tags = split_comma_param(query.locus_tags) if query.locus_tags else []
        uniprot_ids = split_comma_param(query.uniprot_ids) if query.uniprot_ids else []
        
        has_identifiers = locus_tags or uniprot_ids
        has_filters = any([
            query.media,
            query.experimental_condition,
            query.min_doubling_time,
            query.max_doubling_time,
            query.exclude_double_picked
        ])
        
        if not has_identifiers and not has_filters:
            raise_validation_error(
                "At least one search criterion must be provided: "
                "locus_tags, uniprot_ids, or filter parameters"
            )
        
        total_identifiers = len(locus_tags) + len(uniprot_ids)
        if total_identifiers > 1000:
            raise_validation_error("Maximum 1000 total identifiers allowed per search request")
        
        results = await mutant_growth_service.search_with_filters(
            locus_tags=locus_tags,
            uniprot_ids=uniprot_ids,
            media=query.media,
            experimental_condition=query.experimental_condition,
            min_doubling_time=query.min_doubling_time,
            max_doubling_time=query.max_doubling_time,
            exclude_double_picked=query.exclude_double_picked,
        )
        
        return create_success_response(
            data=results,
            message=f"Found {len(results)} genes with mutant growth data"
        )
    except ServiceError as e:
        logger.error(f"Service error in mutant growth search: {e}")
        raise_internal_server_error(f"Failed to search mutant growth data: {str(e)}")

