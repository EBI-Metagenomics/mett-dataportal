"""POST /ppi/paths — shortest paths between 2–5 genes."""

import logging

from ninja import Router

from dataportal.authentication import APIRoles, RoleBasedJWTAuth
from dataportal.schema.interactions.ppi_path_schemas import (
    PPIPathsQuerySchema,
    PPIPathsResponseSchema,
)
from dataportal.schema.response_schemas import ErrorCode, create_success_response
from dataportal.services.interactions.ppi_paths import PPIPathService
from dataportal.utils.errors import (
    raise_internal_server_error,
    raise_not_found_error,
    raise_validation_error,
)
from dataportal.utils.exceptions import ServiceError, ValidationError
from dataportal.utils.response_wrappers import wrap_success_response

logger = logging.getLogger(__name__)

ppi_path_service = PPIPathService()


def register_ppi_path_routes(router: Router) -> None:
    """Mount path search on the PPI router. Neighborhood routes are unchanged."""

    @router.post(
        "/paths",
        response=PPIPathsResponseSchema,
        summary="Shortest paths between genes of interest",
        description=(
            "Find the shortest METT interaction path between each pair in a set of "
            "2 to 5 locus tags. Paths are at most two steps. Pairs with no path are listed "
            "and do not remove paths that were found."
        ),
        auth=RoleBasedJWTAuth(required_roles=[APIRoles.PPI]),
    )
    @wrap_success_response
    async def find_ppi_paths(request, payload: PPIPathsQuerySchema):
        try:
            data = await ppi_path_service.find_paths(
                locus_tags=payload.locus_tags,
                species_acronym=payload.species_acronym,
                score_type=payload.score_type,
                score_threshold=payload.score_threshold,
            )
            return create_success_response(
                data=data,
                message="PPI paths retrieved successfully",
            )
        except ValidationError as exc:
            raise_validation_error(str(exc))
        except ServiceError as exc:
            message = str(exc)
            if "not found" in message.lower():
                raise_not_found_error(message, error_code=ErrorCode.PPI_NOT_FOUND)
            raise_validation_error(message)
        except Exception as exc:
            logger.error("PPI path search failed: %s", exc)
            raise_internal_server_error(f"Failed to find PPI paths: {exc}")
