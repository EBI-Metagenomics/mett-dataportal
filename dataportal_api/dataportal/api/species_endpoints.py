import logging
from typing import List, Optional

from ninja import Router, Query, Path
from ninja.errors import HttpError

from ..schemas import (
    SpeciesSchema,
    GenomePaginationSchema,
)
from ..services.genome_service import GenomeService
from ..services.species_service import SpeciesService
from ..utils.constants import (
    DEFAULT_PER_PAGE_CNT,
    DEFAULT_SORT,
    STRAIN_FIELD_ISOLATE_NAME, )
from ..utils.errors import raise_http_error
from ..utils.exceptions import (
    ServiceError,
)

logger = logging.getLogger(__name__)

species_service = SpeciesService()
genome_service = GenomeService()

ROUTER_SPECIES = "Species"
species_router = Router(tags=[ROUTER_SPECIES])


# API Endpoint to retrieve all species
@species_router.get("/", response=List[SpeciesSchema],
                    summary="Get all species",
                    description="Get all available species"
                    )
async def get_all_species(request):
    try:
        species = await species_service.get_all_species()
        return species
    except ServiceError:
        raise HttpError(500, "An error occurred while fetching species.")
    except Exception:
        raise_http_error(500, "An error occurred while fetching species.")


# API Endpoint to retrieve genomes filtered by species_acronym
@species_router.get(
    "/{species_acronym}/genomes",
    response=GenomePaginationSchema,
    summary="Get genomes by species",
    description=(
            "Retrieves a paginated list of genomes that belong to the specified species. "
            "Supports optional sorting by 'isolate_name' or 'species'. "
            "Useful for browsing all genomes under a given species acronym."
    )
)
async def get_genomes_by_species(
        request,
        species_acronym: str = Path(..., description="Acronym for the species (BU or PV)."),
        page: int = Query(1, description="Page number to retrieve."),
        per_page: int = Query(DEFAULT_PER_PAGE_CNT, description="Number of genomes to return per page."),
        sortField: Optional[str] = Query(STRAIN_FIELD_ISOLATE_NAME, description="Field to sort results by."),
        sortOrder: Optional[str] = Query(DEFAULT_SORT, description="Sort order: 'asc' or 'desc'."),
):
    try:
        return await genome_service.get_genomes_by_species(
            species_acronym, page, per_page, sortField, sortOrder
        )
    except ServiceError:
        raise HttpError(
            500, f"An error occurred while fetching genomes by species: {species_acronym}"
        )


# API Endpoint to search genomes by species_acronym and query string
@species_router.get(
    "/{species_acronym}/genomes/search",
    response=GenomePaginationSchema,
    summary="Search genomes by species and query string",
    description=(
            "Performs a search for genomes within a specific species using a free-text query. "
            "Returns a paginated list of matching genome records. "
            "Useful for narrowing down results within a species context, with optional sorting by 'isolate_name' or 'species'."
    )
)
async def search_genomes_by_species_and_string(
        request,
        species_acronym: str = Path(..., description="Acronym for the species (BU or PV)."),
        query: str = Query(..., description="Search term to match against genome names or metadata."),
        page: int = Query(1, description="Page number to retrieve."),
        per_page: int = Query(DEFAULT_PER_PAGE_CNT, description="Number of genomes to return per page."),
        sortField: Optional[str] = Query(STRAIN_FIELD_ISOLATE_NAME, description="Field to sort results by."),
        sortOrder: Optional[str] = Query(DEFAULT_SORT, description="Sort order: 'asc' or 'desc'."),
):
    try:
        return await genome_service.search_genomes_by_species_and_string(
            species_acronym, query, page, per_page, sortField, sortOrder
        )
    except ServiceError:
        raise HttpError(
            500,
            f"An error occurred while fetching genomes by species: {species_acronym} and query: {query}",
        )
