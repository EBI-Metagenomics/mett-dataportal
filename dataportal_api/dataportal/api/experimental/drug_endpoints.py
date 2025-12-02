"""
Drug-specific API endpoints for MIC and metabolism data.
"""

import logging

from ninja import Router, Query, Path

from dataportal.api.core import genome_router
from dataportal.authentication import APIRoles, RoleBasedJWTAuth
from dataportal.schema.experimental.drug_schemas import (
    DrugMICSearchQuerySchema,
    DrugMetabolismSearchQuerySchema,
    DrugAutocompleteQuerySchema,
    PaginatedStrainDrugMICResponseSchema,
    PaginatedStrainDrugMetabolismResponseSchema,
    StrainDrugDataResponseSchema,
    DrugMICPaginationSchema,
    DrugMetabolismPaginationSchema,
)
from dataportal.schema.response_schemas import (
    PaginatedResponseSchema,
    SuccessResponseSchema,
    ErrorCode,
    create_success_response,
)
from dataportal.services.experimental.drug_service import DrugService
from dataportal.utils.errors import raise_internal_server_error, raise_not_found_error
from dataportal.utils.exceptions import ServiceError
from dataportal.utils.response_wrappers import wrap_paginated_response, wrap_success_response

logger = logging.getLogger(__name__)

drug_service = DrugService()

ROUTER_DRUG = "Drugs"
drug_router = Router(tags=[ROUTER_DRUG])


# Drug data endpoints for strains
@genome_router.get(
    "/{isolate_name}/drug-mic",
    response=PaginatedStrainDrugMICResponseSchema,
    summary="Get drug MIC data for a strain",
    description=(
        "Retrieves drug MIC (Minimum Inhibitory Concentration) data for a specific strain. "
        "Returns paginated MIC measurements including drug names, values, units, and experimental conditions."
    ),
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.DRUGS]),
)
async def get_strain_drug_mic(
    request,
    isolate_name: str = Path(..., description="Strain isolate name"),
    page: int = Query(1, description="Page number", ge=1),
    per_page: int = Query(20, description="Number of results per page", ge=1, le=100),
):
    """Get paginated drug MIC data for a specific strain."""
    try:
        result = await drug_service.get_strain_drug_mic_paginated(isolate_name, page, per_page)
        if not result:
            raise_not_found_error(
                message=f"No drug MIC data found for strain: {isolate_name}",
                error_code=ErrorCode.DRUG_DATA_NOT_FOUND,
            )
        return result
    except ServiceError as e:
        logger.error(f"Service error getting drug MIC data for {isolate_name}: {e}")
        raise_internal_server_error(f"Failed to retrieve drug MIC data: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error getting drug MIC data for {isolate_name}: {e}")
        raise_internal_server_error(f"Failed to retrieve drug MIC data: {str(e)}")


@genome_router.get(
    "/{isolate_name}/drug-metabolism",
    response=PaginatedStrainDrugMetabolismResponseSchema,
    summary="Get drug metabolism data for a strain",
    description=(
        "Retrieves drug metabolism data for a specific strain. "
        "Returns paginated degradation percentages, statistical significance, and metabolizer classifications."
    ),
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.DRUGS]),
)
async def get_strain_drug_metabolism(
    request,
    isolate_name: str = Path(..., description="Strain isolate name"),
    page: int = Query(1, description="Page number", ge=1),
    per_page: int = Query(20, description="Number of results per page", ge=1, le=100),
):
    """Get paginated drug metabolism data for a specific strain."""
    try:
        result = await drug_service.get_strain_drug_metabolism_paginated(
            isolate_name, page, per_page
        )
        if not result:
            raise_not_found_error(
                message=f"No drug metabolism data found for strain: {isolate_name}",
                error_code=ErrorCode.DRUG_DATA_NOT_FOUND,
            )
        return result
    except ServiceError as e:
        logger.error(f"Service error getting drug metabolism data for {isolate_name}: {e}")
        raise_internal_server_error(f"Failed to retrieve drug metabolism data: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error getting drug metabolism data for {isolate_name}: {e}")
        raise_internal_server_error(f"Failed to retrieve drug metabolism data: {str(e)}")


@genome_router.get(
    "/{isolate_name}/drug-data",
    response=StrainDrugDataResponseSchema,
    summary="Get all drug data for a strain",
    description=(
        "Retrieves both drug MIC and metabolism data for a specific strain. "
        "Returns comprehensive drug response information including resistance and metabolism patterns. "
        "No pagination is applied as this endpoint returns complete datasets for both MIC and metabolism data."
    ),
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.DRUGS]),
)
async def get_strain_drug_data(
    request, isolate_name: str = Path(..., description="Strain isolate name")
):
    """Get all drug data (MIC + metabolism) for a specific strain."""
    try:
        result = await drug_service.get_strain_drug_data(isolate_name)
        if not result:
            raise_not_found_error(
                message=f"No drug data found for strain: {isolate_name}",
                error_code=ErrorCode.DRUG_DATA_NOT_FOUND,
            )
        return result
    except ServiceError as e:
        logger.error(f"Service error getting drug data for {isolate_name}: {e}")
        raise_internal_server_error(f"Failed to retrieve drug data: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error getting drug data for {isolate_name}: {e}")
        raise_internal_server_error(f"Failed to retrieve drug data: {str(e)}")


# Drug MIC endpoints
@drug_router.get(
    "/mic/search",
    response=PaginatedResponseSchema,
    summary="Search drug MIC data",
    description=(
        "Search drug MIC (Minimum Inhibitory Concentration) data across all strains. "
        "Supports filtering by drug name, class, species, MIC values, and experimental conditions. "
        "Returns paginated results with detailed MIC measurements. "
        "Note: Sorting is limited to top-level fields (isolate_name, species_acronym, species_scientific_name)."
    ),
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.DRUGS]),
)
@wrap_paginated_response
async def search_drug_mic(request, query: DrugMICSearchQuerySchema = Query(...)):
    """Search drug MIC data across strains."""
    try:
        result = await drug_service.search_drug_mic(query)
        return result
    except ServiceError as e:
        logger.error(f"Service error searching drug MIC data: {e}")
        raise_internal_server_error(f"Failed to search drug MIC data: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error searching drug MIC data: {e}")
        raise_internal_server_error(f"Failed to search drug MIC data: {str(e)}")


@drug_router.get(
    "/mic/by-drug/{drug_name}",
    response=PaginatedResponseSchema,
    summary="Get MIC data by drug name",
    description=(
        "Retrieves MIC data for a specific drug across all strains. "
        "Supports pagination and optional species filtering."
    ),
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.DRUGS]),
)
@wrap_paginated_response
async def get_drug_mic_by_drug(
    request,
    drug_name: str = Path(..., description="Name of the drug"),
    species_acronym: str = Query(None, description="Optional species acronym filter (BU, PV)"),
    page: int = Query(1, description="Page number", ge=1),
    per_page: int = Query(20, description="Number of results per page", ge=1, le=100),
):
    """Get paginated MIC data for a specific drug."""
    try:
        # Get all MIC records for this drug, then paginate at the record level
        all_results = await drug_service.get_drug_mic_by_drug(drug_name, species_acronym)

        total_results = len(all_results)
        total_pages = (total_results + per_page - 1) // per_page if total_results > 0 else 1
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        page_results = all_results[start_index:end_index]

        return DrugMICPaginationSchema(
            results=page_results,
            page_number=page,
            num_pages=total_pages,
            has_previous=page > 1,
            has_next=page < total_pages,
            total_results=total_results,
        )
    except ServiceError as e:
        logger.error(f"Service error getting MIC data for drug {drug_name}: {e}")
        raise_internal_server_error(f"Failed to retrieve MIC data for drug: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error getting MIC data for drug {drug_name}: {e}")
        raise_internal_server_error(f"Failed to retrieve MIC data for drug: {str(e)}")


@drug_router.get(
    "/mic/by-class/{drug_class}",
    response=PaginatedResponseSchema,
    summary="Get MIC data by drug class",
    description=(
        "Retrieves all MIC data for a specific drug class across all strains. "
        "Supports pagination and optional species filtering."
    ),
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.DRUGS]),
    include_in_schema=False,
)
@wrap_paginated_response
async def get_drug_mic_by_class(
    request,
    drug_class: str = Path(..., description="Drug class (e.g., beta_lactam)"),
    species_acronym: str = Query(None, description="Optional species acronym filter (BU, PV)"),
    page: int = Query(1, description="Page number"),
    per_page: int = Query(20, description="Number of results per page"),
):
    """Get all MIC data for a specific drug class."""
    try:
        query = DrugMICSearchQuerySchema(
            query="",
            drug_class=drug_class,
            species_acronym=species_acronym,
            page=page,
            per_page=per_page,
        )
        result = await drug_service.search_drug_mic(query)
        return result
    except ServiceError as e:
        logger.error(f"Service error getting MIC data for drug class {drug_class}: {e}")
        raise_internal_server_error(f"Failed to retrieve MIC data for drug class: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error getting MIC data for drug class {drug_class}: {e}")
        raise_internal_server_error(f"Failed to retrieve MIC data for drug class: {str(e)}")


# Drug metabolism endpoints
@drug_router.get(
    "/metabolism/search",
    response=PaginatedResponseSchema,
    summary="Search drug metabolism data",
    description=(
        "Search drug metabolism data across all strains. "
        "Supports filtering by drug name, class, species, statistical significance, "
        "degradation percentages, and experimental conditions. "
        "Returns paginated results with detailed metabolism measurements. "
        "Note: Sorting is limited to top-level fields (isolate_name, species_acronym, species_scientific_name)."
    ),
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.DRUGS]),
)
@wrap_paginated_response
async def search_drug_metabolism(request, query: DrugMetabolismSearchQuerySchema = Query(...)):
    """Search drug metabolism data across strains."""
    try:
        result = await drug_service.search_drug_metabolism(query)
        return result
    except ServiceError as e:
        logger.error(f"Service error searching drug metabolism data: {e}")
        raise_internal_server_error(f"Failed to search drug metabolism data: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error searching drug metabolism data: {e}")
        raise_internal_server_error(f"Failed to search drug metabolism data: {str(e)}")


@drug_router.get(
    "/metabolism/by-drug/{drug_name}",
    response=PaginatedResponseSchema,
    summary="Get metabolism data by drug name",
    description=(
        "Retrieves metabolism data for a specific drug across all strains. "
        "Supports pagination and optional species filtering."
    ),
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.DRUGS]),
)
@wrap_paginated_response
async def get_drug_metabolism_by_drug(
    request,
    drug_name: str = Path(..., description="Name of the drug"),
    species_acronym: str = Query(None, description="Optional species acronym filter (BU, PV)"),
    page: int = Query(1, description="Page number", ge=1),
    per_page: int = Query(20, description="Number of results per page", ge=1, le=100),
):
    """Get paginated metabolism data for a specific drug."""
    try:
        # Get all metabolism records for this drug, then paginate at the record level
        all_results = await drug_service.get_drug_metabolism_by_drug(drug_name, species_acronym)

        total_results = len(all_results)
        total_pages = (total_results + per_page - 1) // per_page if total_results > 0 else 1
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        page_results = all_results[start_index:end_index]

        return DrugMetabolismPaginationSchema(
            results=page_results,
            page_number=page,
            num_pages=total_pages,
            has_previous=page > 1,
            has_next=page < total_pages,
            total_results=total_results,
        )
    except ServiceError as e:
        logger.error(f"Service error getting metabolism data for drug {drug_name}: {e}")
        raise_internal_server_error(f"Failed to retrieve metabolism data for drug: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error getting metabolism data for drug {drug_name}: {e}")
        raise_internal_server_error(f"Failed to retrieve metabolism data for drug: {str(e)}")


@drug_router.get(
    "/metabolism/by-class/{drug_class}",
    response=PaginatedResponseSchema,
    summary="Get metabolism data by drug class",
    description=(
        "Retrieves all metabolism data for a specific drug class across all strains. "
        "Supports pagination and optional species filtering."
    ),
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.DRUGS]),
    include_in_schema=False,
)
@wrap_paginated_response
async def get_drug_metabolism_by_class(
    request,
    drug_class: str = Path(..., description="Drug class (e.g., beta_lactam)"),
    species_acronym: str = Query(None, description="Optional species acronym filter (BU, PV)"),
    page: int = Query(1, description="Page number"),
    per_page: int = Query(20, description="Number of results per page"),
):
    """Get all metabolism data for a specific drug class."""
    try:
        query = DrugMetabolismSearchQuerySchema(
            query="",
            drug_class=drug_class,
            species_acronym=species_acronym,
            page=page,
            per_page=per_page,
        )
        result = await drug_service.search_drug_metabolism(query)
        return result
    except ServiceError as e:
        logger.error(f"Service error getting metabolism data for drug class {drug_class}: {e}")
        raise_internal_server_error(f"Failed to retrieve metabolism data for drug class: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error getting metabolism data for drug class {drug_class}: {e}")
        raise_internal_server_error(f"Failed to retrieve metabolism data for drug class: {str(e)}")


# Drug autocomplete endpoint
@drug_router.get(
    "/autocomplete",
    response=SuccessResponseSchema,
    summary="Get drug name suggestions",
    description=(
        "Get drug name suggestions for autocomplete functionality. "
        "Supports fuzzy matching and partial search. "
        "Can filter by species and data type (MIC or metabolism)."
    ),
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.DRUGS]),
    include_in_schema=False,
)
@wrap_success_response
async def get_drug_suggestions(request, query: DrugAutocompleteQuerySchema = Query(...)):
    """Get drug name suggestions for autocomplete."""
    try:
        results = await drug_service.get_drug_suggestions(query)
        return create_success_response(
            data=results, message=f"Found {len(results)} drug suggestions"
        )
    except ServiceError as e:
        logger.error(f"Service error getting drug suggestions: {e}")
        raise_internal_server_error(f"Failed to retrieve drug suggestions: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error getting drug suggestions: {e}")
        raise_internal_server_error(f"Failed to retrieve drug suggestions: {str(e)}")
