"""List METT Elasticsearch releases for the portal version selector."""

from ninja import Router, Schema

from dataportal.elasticsearch.names import CURRENT_TOKEN, INDEX_FAMILIES, current_alias_name
from dataportal.elasticsearch.resolver import selected_release
from dataportal.models.releases import MettRelease
from dataportal.schema.response_schemas import SuccessResponseSchema, create_success_response
from dataportal.utils.response_wrappers import wrap_success_response

release_router = Router(tags=["Releases"])


class ReleaseFamilySchema(Schema):
    family: str
    alias: str
    physical_index: str
    generation: int
    adopted_legacy: bool


class ReleaseSchema(Schema):
    version: str
    status: str
    is_current: bool
    promoted_at: str | None = None
    archived_at: str | None = None
    families: list[ReleaseFamilySchema]


class ReleaseListSchema(Schema):
    default: str
    selected: str
    current_version: str | None = None
    releases: list[ReleaseSchema]


def _serialize_release(rel: MettRelease, current_version: str | None) -> dict:
    families = []
    by_family = {row.family: row for row in rel.indexes.all()}
    for fam in INDEX_FAMILIES:
        row = by_family.get(fam)
        if not row:
            continue
        families.append(
            {
                "family": row.family,
                "alias": row.alias,
                "physical_index": row.physical_index,
                "generation": row.generation,
                "adopted_legacy": row.adopted_legacy,
            }
        )
    return {
        "version": rel.version,
        "status": rel.status,
        "is_current": current_version == rel.version,
        "promoted_at": rel.promoted_at.isoformat() if rel.promoted_at else None,
        "archived_at": rel.archived_at.isoformat() if rel.archived_at else None,
        "families": families,
    }


@release_router.get(
    "",
    summary="List METT data releases",
    description=(
        "Scientist-visible Elasticsearch release sets. "
        "Pass X-METT-Release or ?release=v1 to read an archived or ready set. "
        "'current' follows whichever release is promoted."
    ),
    response=SuccessResponseSchema,
)
@wrap_success_response
def list_releases(request):
    readable = (
        MettRelease.objects.filter(
            status__in=(
                MettRelease.Status.READY,
                MettRelease.Status.CURRENT,
                MettRelease.Status.ARCHIVED,
                MettRelease.Status.BUILDING,
            )
        )
        .prefetch_related("indexes")
        .order_by("-created_at")
    )
    current = next((r for r in readable if r.status == MettRelease.Status.CURRENT), None)
    current_version = current.version if current else None
    payload = {
        "default": CURRENT_TOKEN,
        "selected": selected_release(),
        "current_version": current_version,
        "current_aliases": {fam: current_alias_name(fam) for fam in INDEX_FAMILIES},
        "releases": [_serialize_release(r, current_version) for r in readable],
    }
    return create_success_response(
        data=payload,
        message=f"Retrieved {len(payload['releases'])} METT release(s)",
    )
