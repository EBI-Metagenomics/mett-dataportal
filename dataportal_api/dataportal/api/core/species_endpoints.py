import logging
from typing import List

from ninja import Router, Query, Path
from ninja.errors import HttpError

from dataportal.schema.core.genome_schemas import (
    GenomeSearchQuerySchema,
)
from dataportal.schema.core.species_schemas import (
    SpeciesSchema,
)
from dataportal.schema.response_schemas import PaginatedResponseSchema
from dataportal.services.service_factory import ServiceFactory
from dataportal.utils.errors import raise_http_error, raise_internal_server_error
from dataportal.utils.exceptions import (
    ServiceError,
)
from dataportal.utils.response_wrappers import wrap_paginated_response

logger = logging.getLogger(__name__)

species_service = ServiceFactory.get_species_service()
genome_service = ServiceFactory.get_genome_service()

ROUTER_SPECIES = "Species"
species_router = Router(tags=[ROUTER_SPECIES])


# API Endpoint to retrieve all species
@species_router.get(
    "/",
    response=List[SpeciesSchema],
    summary="Get all species",
    description="Get all available species",
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
    response=PaginatedResponseSchema,
    summary="Get genomes by species",
    description="Retrieves genomes under a given species with pagination and sorting.",
)
@wrap_paginated_response
async def get_genomes_by_species(
    request,
    species_acronym: str = Path(..., description="Acronym for the species (BU or PV)."),
    query: GenomeSearchQuerySchema = Query(...),
):
    try:
        query.species_acronym = species_acronym
        # Clear any existing query to get all genomes for the species
        query.query = ""
        result = await genome_service.search_genomes_by_string(query)
        return result
    except ServiceError as e:
        logger.error(f"Service error in get genomes by species: {e}")
        raise_internal_server_error(
            f"Failed to fetch genomes by species: {species_acronym}"
        )


# API Endpoint to search genomes by species_acronym and query string
@species_router.get(
    "/{species_acronym}/genomes/search",
    response=PaginatedResponseSchema,
    summary="Search genomes by species and query string",
    description="Performs a search for genomes within a specific species with pagination and sorting.",
)
@wrap_paginated_response
async def search_genomes_by_species_and_string(
    request,
    species_acronym: str = Path(..., description="Acronym for the species (BU or PV)."),
    query: GenomeSearchQuerySchema = Query(...),
):
    try:
        query.species_acronym = species_acronym
        result = await genome_service.search_genomes_by_string(query)
        return result
    except ServiceError as e:
        logger.error(f"Service error in search genomes by species: {e}")
        raise_internal_server_error(
            f"Failed to search genomes by species: {species_acronym}"
        )
