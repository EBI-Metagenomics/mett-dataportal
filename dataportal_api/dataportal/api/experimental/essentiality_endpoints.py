import logging
from typing import Optional

from ninja import Router, Query, Path

from dataportal.api.core.gene_endpoints import gene_router
from dataportal.schema.experimental.essentiality_schemas import EssentialitySearchQuerySchema
from dataportal.schema.response_schemas import SuccessResponseSchema, create_success_response
from dataportal.services.experimental.essentiality_service import EssentialityService
from dataportal.utils.errors import raise_not_found_error, raise_internal_server_error, raise_validation_error
from dataportal.utils.exceptions import GeneNotFoundError, ServiceError
from dataportal.utils.response_wrappers import wrap_success_response
from dataportal.utils.utils import split_comma_param

logger = logging.getLogger(__name__)

essentiality_service = EssentialityService()

ROUTER_ESSENTIALITY = "Essentiality"
essentiality_router = Router(tags=[ROUTER_ESSENTIALITY])


@gene_router.get(
    "/{locus_tag}/essentiality",
    response=SuccessResponseSchema,
    summary="Get essentiality data for a gene",
    description=(
        "Retrieves essentiality data for a specific gene using its locus tag or UniProt ID. "
        "Returns basic gene information along with essentiality data including TnSeq metrics, "
        "essentiality calls, and experimental conditions."
    ),
    include_in_schema=False,
)
@wrap_success_response
async def get_essentiality_by_gene(
    request,
    locus_tag: str = Path(..., description="Gene locus tag or UniProt ID"),
):
    """Get essentiality data for a specific gene."""
    try:
        result = await essentiality_service.get_by_id(locus_tag)
        
        if not result.essentiality_data or len(result.essentiality_data) == 0:
            return create_success_response(
                data=result,
                message=f"No essentiality data found for gene {locus_tag}"
            )
        
        return create_success_response(
            data=result,
            message=f"Essentiality data for gene {locus_tag} retrieved successfully"
        )
    except GeneNotFoundError as e:
        logger.error(f"Gene not found: {locus_tag}")
        raise_not_found_error(
            f"Gene with identifier '{locus_tag}' not found",
            error_code="GENE_NOT_FOUND"
        )
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise_internal_server_error(f"Failed to fetch essentiality data for '{locus_tag}'")


@essentiality_router.get(
    "/search",
    response=SuccessResponseSchema,
    summary="Search essentiality data with filters",
    description=(
        "Search for essentiality data across genes with optional filters. "
        "Supports identifier-based search and discovery mode (filter-only queries)."
    ),
    include_in_schema=False,
)
@wrap_success_response
async def search_essentiality(
    request,
    query: EssentialitySearchQuerySchema = Query(...),
):
    """Search for essentiality data by identifiers and/or filters."""
    try:
        locus_tags = split_comma_param(query.locus_tags) if query.locus_tags else []
        uniprot_ids = split_comma_param(query.uniprot_ids) if query.uniprot_ids else []
        
        has_identifiers = locus_tags or uniprot_ids
        has_filters = any([
            query.essentiality_call,
            query.experimental_condition,
            query.min_tas_in_locus,
            query.min_tas_hit,
            query.element
        ])
        
        if not has_identifiers and not has_filters:
            raise_validation_error(
                "At least one search criterion must be provided: "
                "locus_tags, uniprot_ids, or filter parameters"
            )
        
        total_identifiers = len(locus_tags) + len(uniprot_ids)
        if total_identifiers > 1000:
            raise_validation_error("Maximum 1000 total identifiers allowed per search request")
        
        results = await essentiality_service.search_with_filters(
            locus_tags=locus_tags,
            uniprot_ids=uniprot_ids,
            essentiality_call=query.essentiality_call,
            experimental_condition=query.experimental_condition,
            min_tas_in_locus=query.min_tas_in_locus,
            min_tas_hit=query.min_tas_hit,
            element=query.element,
        )
        
        return create_success_response(
            data=results,
            message=f"Found {len(results)} genes with essentiality data"
        )
    except ServiceError as e:
        logger.error(f"Service error in essentiality search: {e}")
        raise_internal_server_error(f"Failed to search essentiality data: {str(e)}")

