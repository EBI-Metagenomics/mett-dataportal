import logging
from typing import Optional
from ninja import Router, Query
from ninja.errors import HttpError

from dataportal.schema.ppi_schemas import (
    PPISearchQuerySchema,
    PPISearchResponseSchema,
    PPINetworkResponseSchema,
    PPINetworkPropertiesResponseSchema,
    PPINeighborhoodResponseSchema,
)
from dataportal.services.ppi_service import PPIService
from dataportal.schema.response_schemas import create_success_response, create_error_response, SuccessResponseSchema
from dataportal.utils.exceptions import ServiceError, ValidationError
from dataportal.utils.response_wrappers import wrap_paginated_response, wrap_success_response

logger = logging.getLogger(__name__)

ROUTER_PPI = "Protein-Protein Interactions"
ppi_router = Router(tags=[ROUTER_PPI])

# Initialize service
ppi_service = PPIService()


@ppi_router.get(
    "/interactions/{protein_id}",
    summary="Get protein interactions",
    description="Get all interactions for a specific protein"
)
async def get_protein_interactions(
        request,
        protein_id: str,
        species_acronym: Optional[str] = None
):
    """Get all interactions for a specific protein."""
    logger.info(f"Get protein interactions for {protein_id}")
    logger.info(f"species acronym: {species_acronym}")
    try:
        interactions = await ppi_service.get_protein_interactions(
            protein_id=protein_id,
            species_acronym=species_acronym
        )

        return create_success_response(
            data=interactions,
            message=f"Interactions for protein {protein_id} retrieved successfully"
        )
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise HttpError(500, f"Failed to get protein interactions: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HttpError(500, "Internal server error")


@ppi_router.get(
    "/interactions",
    response=PPISearchResponseSchema,
    summary="Search protein-protein interactions",
    description="Search for protein-protein interactions with various filtering options"
)
@wrap_paginated_response
async def search_ppi_interactions(request, query: PPISearchQuerySchema = Query(...)):
    """Search for PPI interactions based on query parameters."""
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
    "/network/{score_type}",
    response=PPINetworkResponseSchema,
    summary="Get PPI network data",
    description="Get network data for a specific score type and threshold"
)
@wrap_success_response
async def get_ppi_network(
    request,
    score_type: str,
    score_threshold: float = 0.8,
    species_acronym: Optional[str] = None,
    include_properties: bool = False
):
    """Get PPI network data for a specific score type and threshold."""
    try:
        network_data = await ppi_service.get_network_data(
            score_type=score_type,
            score_threshold=score_threshold,
            species_acronym=species_acronym
        )
        
        # Include properties if requested
        if include_properties:
            properties = await ppi_service.get_network_properties(
                score_type=score_type,
                score_threshold=score_threshold,
                species_acronym=species_acronym
            )
            network_data.properties = properties
        
        return create_success_response(
            data=network_data,
            message=f"Network data for {score_type} (threshold: {score_threshold}) retrieved successfully"
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
    description="Get network properties (nodes, edges, density, clustering) for a specific score type and threshold"
)
@wrap_success_response
async def get_ppi_network_properties(
    request,
    score_type: str,
    score_threshold: float = 0.8,
    species_acronym: Optional[str] = None
):
    """Get PPI network properties for a specific score type and threshold."""
    try:
        properties = await ppi_service.get_network_properties(
            score_type=score_type,
            score_threshold=score_threshold,
            species_acronym=species_acronym
        )
        
        return create_success_response(
            data=properties,
            message=f"Network properties for {score_type} (threshold: {score_threshold}) retrieved successfully"
        )
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise HttpError(500, f"Failed to get network properties: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HttpError(500, "Internal server error")


@ppi_router.get(
    "/neighborhood/{protein_id}",
    response=PPINeighborhoodResponseSchema,
    summary="Get protein neighborhood",
    description="Get neighborhood data for a specific protein"
)
@wrap_success_response
async def get_protein_neighborhood(
    request,
    protein_id: str,
    n: int = 5,
    species_acronym: Optional[str] = None
):
    """Get neighborhood data for a specific protein."""
    try:
        neighborhood = await ppi_service.get_protein_neighborhood(
            protein_id=protein_id,
            n=n,
            species_acronym=species_acronym
        )
        
        return create_success_response(
            data=neighborhood,
            message=f"Neighborhood data for protein {protein_id} retrieved successfully"
        )
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise HttpError(500, f"Failed to get protein neighborhood: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HttpError(500, "Internal server error")



@ppi_router.get(
    "/scores/available",
    summary="Get available score types",
    description="Get list of available score types for PPI filtering"
)
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
        
        return {"score_types": score_types}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HttpError(500, "Internal server error")
