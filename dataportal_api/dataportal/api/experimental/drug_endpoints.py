"""
Drug-specific API endpoints for MIC and metabolism data.
"""

import logging
from typing import List

from ninja import Router, Query, Path

from dataportal.schema.experimental.drug_schemas import (
    DrugMICSearchQuerySchema,
    DrugMetabolismSearchQuerySchema,
    DrugMICSearchResultSchema,
    DrugMetabolismSearchResultSchema,
    DrugSuggestionSchema,
    DrugAutocompleteQuerySchema,
)
from dataportal.schema.response_schemas import PaginatedResponseSchema
from dataportal.services.experimental.drug_service import DrugService
from dataportal.utils.errors import raise_internal_server_error
from dataportal.utils.exceptions import ServiceError
from dataportal.utils.response_wrappers import wrap_paginated_response

logger = logging.getLogger(__name__)

drug_service = DrugService()

ROUTER_DRUG = "Drugs"
drug_router = Router(tags=[ROUTER_DRUG])


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
    response=List[DrugMICSearchResultSchema],
    summary="Get MIC data by drug name",
    description=(
            "Retrieves all MIC data for a specific drug across all strains. "
            "Optionally filter by species acronym to narrow results to specific species."
    ),
)
async def get_drug_mic_by_drug(
        request,
        drug_name: str = Path(..., description="Name of the drug"),
        species_acronym: str = Query(None, description="Optional species acronym filter (BU, PV)")
):
    """Get all MIC data for a specific drug."""
    try:
        results = await drug_service.get_drug_mic_by_drug(drug_name, species_acronym)
        return results
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
    ), include_in_schema=False,
)
@wrap_paginated_response
async def get_drug_mic_by_class(
        request,
        drug_class: str = Path(..., description="Drug class (e.g., beta_lactam)"),
        species_acronym: str = Query(None, description="Optional species acronym filter (BU, PV)"),
        page: int = Query(1, description="Page number"),
        per_page: int = Query(20, description="Number of results per page")
):
    """Get all MIC data for a specific drug class."""
    try:
        query = DrugMICSearchQuerySchema(
            query="",
            drug_class=drug_class,
            species_acronym=species_acronym,
            page=page,
            per_page=per_page
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
    response=List[DrugMetabolismSearchResultSchema],
    summary="Get metabolism data by drug name",
    description=(
            "Retrieves all metabolism data for a specific drug across all strains. "
            "Optionally filter by species acronym to narrow results to specific species."
    ),
)
async def get_drug_metabolism_by_drug(
        request,
        drug_name: str = Path(..., description="Name of the drug"),
        species_acronym: str = Query(None, description="Optional species acronym filter (BU, PV)")
):
    """Get all metabolism data for a specific drug."""
    try:
        results = await drug_service.get_drug_metabolism_by_drug(drug_name, species_acronym)
        return results
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
    ), include_in_schema=False,
)
@wrap_paginated_response
async def get_drug_metabolism_by_class(
        request,
        drug_class: str = Path(..., description="Drug class (e.g., beta_lactam)"),
        species_acronym: str = Query(None, description="Optional species acronym filter (BU, PV)"),
        page: int = Query(1, description="Page number"),
        per_page: int = Query(20, description="Number of results per page")
):
    """Get all metabolism data for a specific drug class."""
    try:
        query = DrugMetabolismSearchQuerySchema(
            query="",
            drug_class=drug_class,
            species_acronym=species_acronym,
            page=page,
            per_page=per_page
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
    response=List[DrugSuggestionSchema],
    summary="Get drug name suggestions",
    description=(
            "Get drug name suggestions for autocomplete functionality. "
            "Supports fuzzy matching and partial search. "
            "Can filter by species and data type (MIC or metabolism)."
    ), include_in_schema=False,
)
async def get_drug_suggestions(request, query: DrugAutocompleteQuerySchema = Query(...)):
    """Get drug name suggestions for autocomplete."""
    try:
        results = await drug_service.get_drug_suggestions(query)
        return results
    except ServiceError as e:
        logger.error(f"Service error getting drug suggestions: {e}")
        raise_internal_server_error(f"Failed to retrieve drug suggestions: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error getting drug suggestions: {e}")
        raise_internal_server_error(f"Failed to retrieve drug suggestions: {str(e)}")
