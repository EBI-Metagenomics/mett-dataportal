import logging

from ninja import Router, Query
from ninja.errors import HttpError

from dataportal.authentication import RoleBasedJWTAuth, APIRoles
from dataportal.schema.interactions.ppi_schemas import (
    PPISearchQuerySchema,
    PPISearchResponseSchema,
    PPINetworkResponseSchema,
    PPINetworkPropertiesResponseSchema,
    PPINeighborhoodResponseSchema,
    PPIAllNeighborsResponseSchema,
    PPINeighborhoodQuerySchema,
    PPINeighborsQuerySchema,
    PPINetworkQuerySchema,
    PPINetworkPropertiesQuerySchema,
    PPIScoreTypesResponseSchema,
)
from dataportal.schema.response_schemas import create_success_response
from dataportal.services.interactions.ppi_service import PPIService
from dataportal.utils.exceptions import ServiceError
from dataportal.utils.response_wrappers import wrap_paginated_response, wrap_success_response

logger = logging.getLogger(__name__)

ROUTER_PPI = "Protein-Protein Interactions"
ppi_router = Router(tags=[ROUTER_PPI])

# Initialize service
ppi_service = PPIService()


@ppi_router.get(
    "/scores/available",
    response=PPIScoreTypesResponseSchema,
    summary="Get available score types",
    description="Get list of available score types for PPI filtering",
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.PPI]),
)
@wrap_success_response
async def get_available_score_types(request):
    """Get list of available score types for PPI filtering."""
    try:
        score_types = [
            "ds_score",
            "comelt_score",
            "perturbation_score",
            "abundance_score",
            "melt_score",
            "secondary_score",
            "bayesian_score",
            "string_score",
            "operon_score",
            "ecocyc_score",
            "tt_score"
        ]

        return create_success_response(
            data={"score_types": score_types},
            message="Available score types retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HttpError(500, "Internal server error")


@ppi_router.get(
    "/interactions",
    response=PPISearchResponseSchema,
    summary="Search protein-protein interactions",
    description="Search for protein-protein interactions with various filtering options. Can search by protein_id (UniProt ID) or locus_tag.",
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.PPI]),
)
@wrap_paginated_response
async def search_ppi_interactions(request, query: PPISearchQuerySchema = Query(...)):
    """Search for PPI interactions based on query parameters."""
    # Enhanced validation: ensure at least one search parameter is provided
    has_search_criteria = any([
        query.protein_id, query.locus_tag, query.species_acronym, query.isolate_name,
        query.score_type, query.has_xlms, query.has_string, query.has_operon, query.has_ecocyc
    ])

    if not has_search_criteria:
        raise HttpError(400,
                        "At least one search parameter must be provided. Use protein_id or locus_tag for specific protein searches, or species_acronym for species-wide searches.")

    try:
        result = await ppi_service.search_interactions(query)
        return result
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise HttpError(500, f"Failed to search PPI interactions: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HttpError(500, "Internal server error")


@ppi_router.get(
    "/neighborhood",
    response=PPINeighborhoodResponseSchema,
    summary="Get protein neighborhood",
    description="Get neighborhood data for a specific protein. Can search by protein_id (UniProt ID) or locus_tag.",
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.PPI]),
    include_in_schema=False,
)
@wrap_success_response
async def get_protein_neighborhood(
        request,
        query: PPINeighborhoodQuerySchema = Query(...)
):
    """Get neighborhood data for a specific protein by protein_id or locus_tag."""
    # Validation: exactly one of protein_id or locus_tag must be provided
    if not query.protein_id and not query.locus_tag:
        raise HttpError(400, "Either 'protein_id' or 'locus_tag' must be provided")
    if query.protein_id and query.locus_tag:
        raise HttpError(400, "Only one of 'protein_id' or 'locus_tag' can be provided, not both")

    # Resolve locus_tag to protein_id if needed
    actual_protein_id = query.protein_id
    if query.locus_tag:
        try:
            actual_protein_id = await ppi_service.resolve_locus_tag_to_protein_id(
                locus_tag=query.locus_tag,
                species_acronym=query.species_acronym
            )
            logger.info(f"Resolved locus tag '{query.locus_tag}' to protein_id '{actual_protein_id}'")
        except ServiceError as e:
            logger.error(f"Locus tag resolution error: {e}")
            raise HttpError(404, str(e))

    try:
        neighborhood = await ppi_service.get_protein_neighborhood(
            protein_id=actual_protein_id,
            n=query.n,
            species_acronym=query.species_acronym
        )

        search_identifier = query.locus_tag if query.locus_tag else actual_protein_id
        return create_success_response(
            data=neighborhood,
            message=f"Neighborhood data for {search_identifier} retrieved successfully"
        )
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise HttpError(500, f"Failed to get protein neighborhood: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HttpError(500, "Internal server error")


@ppi_router.get(
    "/neighbors",
    response=PPIAllNeighborsResponseSchema,
    summary="Get all protein neighbors (raw data)",
    description="Get all neighbors for a specific protein without algorithm processing. Returns raw interaction data for custom analysis in Jupyter notebooks. Can search by protein_id (UniProt ID) or locus_tag.",
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.PPI]),
)
@wrap_success_response
async def get_all_protein_neighbors(
        request,
        query: PPINeighborsQuerySchema = Query(...)
):
    """Get all neighbors for a specific protein without algorithm processing."""
    # Validation: exactly one of protein_id or locus_tag must be provided
    if not query.protein_id and not query.locus_tag:
        raise HttpError(400, "Either 'protein_id' or 'locus_tag' must be provided")
    if query.protein_id and query.locus_tag:
        raise HttpError(400, "Only one of 'protein_id' or 'locus_tag' can be provided, not both")

    # Resolve locus_tag to protein_id if needed
    actual_protein_id = query.protein_id
    if query.locus_tag:
        try:
            actual_protein_id = await ppi_service.resolve_locus_tag_to_protein_id(
                locus_tag=query.locus_tag,
                species_acronym=query.species_acronym
            )
            logger.info(f"Resolved locus tag '{query.locus_tag}' to protein_id '{actual_protein_id}'")
        except ServiceError as e:
            logger.error(f"Locus tag resolution error: {e}")
            raise HttpError(404, str(e))

    try:
        neighbors_data = await ppi_service.get_all_protein_neighbors(
            protein_id=actual_protein_id,
            species_acronym=query.species_acronym
        )

        search_identifier = query.locus_tag if query.locus_tag else actual_protein_id
        return create_success_response(
            data=neighbors_data,
            message=f"All neighbors for {search_identifier} retrieved successfully"
        )
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise HttpError(500, f"Failed to get all protein neighbors: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HttpError(500, "Internal server error")


@ppi_router.get(
    "/network/{score_type}",
    response=PPINetworkResponseSchema,
    summary="Get PPI network data",
    description="Get network data for a specific score type and threshold",
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.PPI]),
)
@wrap_success_response
async def get_ppi_network(
        request,
        score_type: str,
        query: PPINetworkQuerySchema = Query(...)
):
    """Get PPI network data for a specific score type and threshold."""
    try:
        network_data = await ppi_service.get_network_data(
            score_type=score_type,
            score_threshold=query.score_threshold,
            species_acronym=query.species_acronym
        )

        # Include properties if requested
        if query.include_properties:
            properties = await ppi_service.get_network_properties(
                score_type=score_type,
                score_threshold=query.score_threshold,
                species_acronym=query.species_acronym
            )
            network_data.properties = properties

        return create_success_response(
            data=network_data,
            message=f"Network data for {score_type} (threshold: {query.score_threshold}) retrieved successfully"
        )
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise HttpError(500, f"Failed to get network data: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HttpError(500, "Internal server error")


@ppi_router.get(
    "/network-properties",
    response=PPINetworkPropertiesResponseSchema,
    summary="Get PPI network properties",
    description="Get network properties (nodes, edges, density, clustering) for a specific score type and threshold",
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.PPI]),
)
@wrap_success_response
async def get_ppi_network_properties(
        request,
        query: PPINetworkPropertiesQuerySchema = Query(...)
):
    """Get PPI network properties for a specific score type and threshold."""
    try:
        properties = await ppi_service.get_network_properties(
            score_type=query.score_type,
            score_threshold=query.score_threshold,
            species_acronym=query.species_acronym
        )

        return create_success_response(
            data=properties,
            message=f"Network properties for {query.score_type} (threshold: {query.score_threshold}) retrieved successfully"
        )
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise HttpError(500, f"Failed to get network properties: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HttpError(500, "Internal server error")
