import logging

from ninja import Router

from dataportal.schema.response_schemas import (
    SuccessResponseSchema,
    create_success_response,
)
from dataportal.utils.cog_categories import COGCategoryService
from dataportal.utils.response_wrappers import wrap_success_response

logger = logging.getLogger(__name__)

cog_cat_service = COGCategoryService()

ROUTER_METADATA = "Metadata"
metadata_router = Router(tags=[ROUTER_METADATA])


@metadata_router.get(
    "/cog-categories",
    summary="List all COG categories",
    description="Returns a list of all standardized COG category codes with their functional descriptions.",
    response=SuccessResponseSchema,
    include_in_schema=False,
)
@wrap_success_response
def get_all_categories(request):
    categories = cog_cat_service.as_list()
    return create_success_response(
        data=categories, message=f"Retrieved {len(categories)} COG categories successfully"
    )
