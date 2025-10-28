import logging
from typing import List, Optional

from ninja import Router, Query, Path

from dataportal.api.core.gene_endpoints import gene_router
from dataportal.authentication import APIRoles, RoleBasedJWTAuth
from dataportal.schema.experimental.proteomics_schemas import (
    ProteomicsWithGeneSchema,
    ProteomicsSearchQuerySchema,
)
from dataportal.schema.response_schemas import (
    SuccessResponseSchema,
    create_success_response,
)
from dataportal.services.experimental.proteomics_service import ProteomicsService
from dataportal.utils.errors import (
    raise_not_found_error,
    raise_internal_server_error,
    raise_validation_error,
)
from dataportal.utils.exceptions import (
    GeneNotFoundError,
    ServiceError,
)
from dataportal.utils.response_wrappers import wrap_success_response
from dataportal.utils.utils import split_comma_param

logger = logging.getLogger(__name__)

proteomics_service = ProteomicsService()

ROUTER_PROTEOMICS = "Proteomics"
proteomics_router = Router(tags=[ROUTER_PROTEOMICS])


@gene_router.get(
    "/{locus_tag}/proteomics",
    response=SuccessResponseSchema,
    summary="Get proteomics evidence for a gene",
    description=(
        "Retrieves proteomics evidence data for a specific gene using its locus tag or UniProt ID. "
        "Returns basic gene information along with all proteomics evidence entries including "
        "coverage, unique peptides, unique intensity, and evidence flag."
    ),
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.PROTEOMICS]),
    include_in_schema=False,
)
@wrap_success_response
async def get_proteomics_by_gene(
    request,
    locus_tag: str = Path(
        ...,
        description="Gene locus tag or UniProt ID (e.g., 'BU_ATCC8492_00001')",
    ),
):
    """Get proteomics evidence data for a specific gene."""
    try:
        result = await proteomics_service.get_by_id(locus_tag)
        
        # Check if proteomics data exists
        if not result.proteomics or len(result.proteomics) == 0:
            return create_success_response(
                data=result,
                message=f"No proteomics evidence found for gene {locus_tag}"
            )
        
        return create_success_response(
            data=result,
            message=f"Proteomics evidence for gene {locus_tag} retrieved successfully"
        )
    except GeneNotFoundError as e:
        logger.error(f"Gene not found: {locus_tag}")
        raise_not_found_error(
            f"Gene with identifier '{locus_tag}' not found",
            error_code="GENE_NOT_FOUND"
        )
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise_internal_server_error(
            f"Failed to fetch proteomics evidence for '{locus_tag}'"
        )


@proteomics_router.get(
    "/search",
    response=SuccessResponseSchema,
    summary="Search proteomics evidence by locus tags and/or UniProt IDs",
    description=(
        "Search for proteomics evidence data across multiple genes using locus tags and/or UniProt IDs. "
        "Supports filtering by minimum coverage, minimum unique peptides, and evidence flag. "
        "Returns an array of genes with their proteomics evidence data."
    ),
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.PROTEOMICS]),
    include_in_schema=False,
)
@wrap_success_response
async def search_proteomics(
    request,
    query: ProteomicsSearchQuerySchema = Query(...),
):
    """Search for proteomics evidence by locus tags and/or UniProt IDs with optional filters."""
    try:
        # Parse comma-separated locus tags and uniprot IDs
        locus_tags = split_comma_param(query.locus_tags) if query.locus_tags else []
        uniprot_ids = split_comma_param(query.uniprot_ids) if query.uniprot_ids else []
        
        # Validate that at least some search criteria is provided
        has_identifiers = locus_tags or uniprot_ids
        has_filters = (
            query.min_coverage is not None or 
            query.min_unique_peptides is not None or 
            query.has_evidence is not None
        )
        
        if not has_identifiers and not has_filters:
            raise_validation_error(
                "At least one search criterion must be provided: "
                "locus_tags, uniprot_ids, or filter parameters (min_coverage, min_unique_peptides, has_evidence)"
            )
        
        # Limit to reasonable number
        total_identifiers = len(locus_tags) + len(uniprot_ids)
        if total_identifiers > 1000:
            raise_validation_error(
                "Maximum 1000 total identifiers allowed per search request"
            )
        
        # Search with filters
        results = await proteomics_service.search_with_filters(
            locus_tags=locus_tags,
            uniprot_ids=uniprot_ids,
            min_coverage=query.min_coverage,
            min_unique_peptides=query.min_unique_peptides,
            has_evidence=query.has_evidence,
        )
        
        return create_success_response(
            data=results,
            message=f"Found {len(results)} genes with proteomics evidence"
        )
    except ServiceError as e:
        logger.error(f"Service error in proteomics search: {e}")
        raise_internal_server_error(
            f"Failed to search proteomics evidence: {str(e)}"
        )
