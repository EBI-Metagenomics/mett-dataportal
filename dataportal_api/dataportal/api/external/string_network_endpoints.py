"""
API endpoints for STRING DB network data.

Provides the /string-network endpoint for fetching STRING DB interaction networks
for PPI pairs or direct STRING protein IDs.
"""

import logging

from ninja import Router, Query

from dataportal.authentication import RoleBasedJWTAuth, APIRoles
from dataportal.schema.external.string_schemas import (
    PPIStringNetworkQuerySchema,
    PPIStringNetworkResponseSchema,
)
from dataportal.schema.response_schemas import create_success_response
from dataportal.services.external.string_network_service import StringNetworkService
from dataportal.utils.constants import PPI_DATA_SOURCE_STRINGDB
from dataportal.utils.exceptions import ServiceError
from dataportal.utils.errors import raise_internal_server_error, raise_validation_error
from dataportal.utils.response_wrappers import wrap_success_response

logger = logging.getLogger(__name__)

string_network_service = StringNetworkService()


def register_string_network_routes(router: Router) -> None:
    """Register STRING network routes on the given router."""

    @router.get(
        "/string-network",
        response=PPIStringNetworkResponseSchema,
        summary="Get STRING DB network for PPI pair",
        description="Fetch STRING DB interaction network for a PPI pair. Provide either pair_id (lookup from PPI index) or protein_ids (STRING protein IDs directly).",
        auth=RoleBasedJWTAuth(required_roles=[APIRoles.PPI]),
    )
    @wrap_success_response
    async def get_string_network(request, query: PPIStringNetworkQuerySchema = Query(...)):
        """Get STRING DB network data for a gene (by locus_tag) or PPI pair."""
        has_locus = bool(query.locus_tag and query.species_acronym)
        has_pair = bool(query.pair_id)
        has_proteins = bool(query.protein_ids)
        if not has_locus and not has_pair and not has_proteins:
            raise_validation_error("Provide locus_tag+species_acronym, pair_id, or protein_ids")
        if sum([has_pair, has_proteins]) > 1:
            raise_validation_error(
                "Only one of 'pair_id' or 'protein_ids' can be provided, not both"
            )

        try:
            result = await string_network_service.get_string_network_for_pair(
                pair_id=query.pair_id if has_pair else None,
                protein_ids=query.protein_ids,
                locus_tag=query.locus_tag,
                species_acronym=query.species_acronym,
                required_score=query.required_score,
                network_type=query.network_type,
                evidence_channels=query.evidence_channels,
            )

            # Tag response with data source metadata for generic multi-source handling.
            existing_sources = result.get("data_sources") or []
            if PPI_DATA_SOURCE_STRINGDB not in existing_sources:
                existing_sources.append(PPI_DATA_SOURCE_STRINGDB)
            result["data_sources"] = existing_sources

            return create_success_response(
                data=result,
                message="STRING network data retrieved successfully",
            )
        except ServiceError as e:
            logger.error(f"Service error: {e}")
            raise_internal_server_error(f"Failed to get STRING network: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise_internal_server_error("Internal server error")
