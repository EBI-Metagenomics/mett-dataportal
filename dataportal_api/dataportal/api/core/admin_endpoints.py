import logging

from ninja import Router

from dataportal.authentication import RoleBasedJWTAuth
from dataportal.authentication.roles import APIRoles
from dataportal.schema.response_schemas import SuccessResponseSchema, create_success_response
from dataportal.utils.response_wrappers import wrap_success_response
from dataportal.utils.species_registry import rebuild as rebuild_species_registry
from dataportal.utils.strain_registry import rebuild as rebuild_strain_registry

logger = logging.getLogger(__name__)

admin_router = Router(tags=["Admin"])


@admin_router.post(
    "/cache/rebuild",
    response=SuccessResponseSchema,
    summary="Rebuild visibility registries",
    description=(
        "Reloads the in-memory enabled-species and enabled-strain caches from Elasticsearch. "
        "Call after species/strain ingest when enablement flags change. "
        "Does not modify Elasticsearch documents."
    ),
    auth=RoleBasedJWTAuth(required_roles=[APIRoles.ADMIN]),
    include_in_schema=False,
)
@wrap_success_response
def rebuild_visibility_cache(request):
    species_count = rebuild_species_registry()
    strain_count = rebuild_strain_registry()
    data = {
        "species_enabled": species_count,
        "strains_enabled": strain_count,
    }
    logger.info("Visibility registries rebuilt: %s", data)
    return create_success_response(
        data=data,
        message="Visibility registries rebuilt successfully",
    )
