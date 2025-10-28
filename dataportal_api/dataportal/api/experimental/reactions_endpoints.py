import logging
from typing import Optional

from ninja import Router, Query, Path

from dataportal.api.core.gene_endpoints import gene_router
from dataportal.authentication import APIRoles, RoleBasedJWTAuth
from dataportal.schema.experimental.reactions_schemas import ReactionsSearchQuerySchema
from dataportal.schema.response_schemas import SuccessResponseSchema, create_success_response
from dataportal.services.experimental.reactions_service import ReactionsService
from dataportal.utils.errors import raise_not_found_error, raise_internal_server_error, raise_validation_error
from dataportal.utils.exceptions import GeneNotFoundError, ServiceError
from dataportal.utils.response_wrappers import wrap_success_response
from dataportal.utils.utils import split_comma_param

logger = logging.getLogger(__name__)

reactions_service = ReactionsService()

ROUTER_REACTIONS = "Reactions"
reactions_router = Router(tags=[ROUTER_REACTIONS])


@gene_router.get(
    "/{locus_tag}/reactions",
    response=SuccessResponseSchema,
    summary="Get reactions data for a gene",
    description=(
        "Retrieves metabolic reactions data for a specific gene using its locus tag or UniProt ID. "
        "Returns basic gene information along with reaction identifiers, GPR rules, and metabolites."
    ),
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.REACTIONS]),
    include_in_schema=False,
)
@wrap_success_response
async def get_reactions_by_gene(
    request,
    locus_tag: str = Path(..., description="Gene locus tag or UniProt ID"),
):
    """Get reactions data for a specific gene."""
    try:
        result = await reactions_service.get_by_id(locus_tag)
        
        if not result.reactions or len(result.reactions) == 0:
            return create_success_response(
                data=result,
                message=f"No reactions data found for gene {locus_tag}"
            )
        
        return create_success_response(
            data=result,
            message=f"Reactions data for gene {locus_tag} retrieved successfully"
        )
    except GeneNotFoundError as e:
        logger.error(f"Gene not found: {locus_tag}")
        raise_not_found_error(
            f"Gene with identifier '{locus_tag}' not found",
            error_code="GENE_NOT_FOUND"
        )
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise_internal_server_error(f"Failed to fetch reactions data for '{locus_tag}'")


@reactions_router.get(
    "/search",
    response=SuccessResponseSchema,
    summary="Search reactions data with filters",
    description=(
        "Search for reactions data across genes with optional filters. "
        "Supports identifier-based search and discovery mode (filter-only queries)."
    ),
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.REACTIONS]),
    include_in_schema=False,
)
@wrap_success_response
async def search_reactions(
    request,
    query: ReactionsSearchQuerySchema = Query(...),
):
    """Search for reactions data by identifiers and/or filters."""
    try:
        locus_tags = split_comma_param(query.locus_tags) if query.locus_tags else []
        uniprot_ids = split_comma_param(query.uniprot_ids) if query.uniprot_ids else []
        
        has_identifiers = locus_tags or uniprot_ids
        has_filters = any([
            query.reaction_id,
            query.metabolite,
            query.substrate,
            query.product
        ])
        
        if not has_identifiers and not has_filters:
            raise_validation_error(
                "At least one search criterion must be provided: "
                "locus_tags, uniprot_ids, or filter parameters"
            )
        
        total_identifiers = len(locus_tags) + len(uniprot_ids)
        if total_identifiers > 1000:
            raise_validation_error("Maximum 1000 total identifiers allowed per search request")
        
        results = await reactions_service.search_with_filters(
            locus_tags=locus_tags,
            uniprot_ids=uniprot_ids,
            reaction_id=query.reaction_id,
            metabolite=query.metabolite,
            substrate=query.substrate,
            product=query.product,
        )
        
        return create_success_response(
            data=results,
            message=f"Found {len(results)} genes with reactions data"
        )
    except ServiceError as e:
        logger.error(f"Service error in reactions search: {e}")
        raise_internal_server_error(f"Failed to search reactions data: {str(e)}")

