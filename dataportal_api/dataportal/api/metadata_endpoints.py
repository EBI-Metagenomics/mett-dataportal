import logging

from ninja import Router

from ..utils.cog_categories import COGCategoryService

logger = logging.getLogger(__name__)

cog_cat_service = COGCategoryService()

ROUTER_METADATA = "Metadata"
metadata_router = Router(tags=[ROUTER_METADATA])


@metadata_router.get(
    "/cog-categories",
    summary="List all COG categories",
    description="Returns a list of all standardized COG category codes with their functional descriptions.",
    response=list[dict[str, str]],
    include_in_schema=False,
)
def get_all_categories(request):
    return cog_cat_service.as_list()
