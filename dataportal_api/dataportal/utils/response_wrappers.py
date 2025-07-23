import asyncio
from typing import Any, Dict, List, Optional
from functools import wraps
import uuid

from dataportal.schema.response_schemas import (
    SuccessResponseSchema,
    PaginatedResponseSchema,
    PaginationMetadataSchema,
    create_success_response,
    create_paginated_response,
)
from dataportal.schema.base_schemas import BasePaginationSchema


def wrap_success_response(func):
    """Decorator to wrap function responses in standardized success format."""

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        result = await func(*args, **kwargs)

        # If result is already a response schema, return as is
        if isinstance(result, (SuccessResponseSchema, PaginatedResponseSchema)):
            return result

        # If result is a pagination schema, convert to paginated response
        if isinstance(result, BasePaginationSchema):
            return create_paginated_response(
                data=result.results,
                pagination=PaginationMetadataSchema(
                    page_number=result.page_number,
                    num_pages=result.num_pages,
                    has_previous=result.has_previous,
                    has_next=result.has_next,
                    total_results=result.total_results,
                    per_page=getattr(result, "per_page", len(result.results)),
                ),
            )

        # Otherwise, wrap in success response
        return create_success_response(data=result)

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        result = func(*args, **kwargs)

        # If result is already a response schema, return as is
        if isinstance(result, (SuccessResponseSchema, PaginatedResponseSchema)):
            return result

        # If result is a pagination schema, convert to paginated response
        if isinstance(result, BasePaginationSchema):
            return create_paginated_response(
                data=result.results,
                pagination=PaginationMetadataSchema(
                    page_number=result.page_number,
                    num_pages=result.num_pages,
                    has_previous=result.has_previous,
                    has_next=result.has_next,
                    total_results=result.total_results,
                    per_page=getattr(result, "per_page", len(result.results)),
                ),
            )

        # Otherwise, wrap in success response
        return create_success_response(data=result)

    # Check if the function is async and return appropriate wrapper
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def wrap_paginated_response(func):
    """Decorator specifically for paginated responses."""

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        result = await func(*args, **kwargs)

        if isinstance(result, PaginatedResponseSchema):
            return result

        if isinstance(result, BasePaginationSchema):
            return create_paginated_response(
                data=result.results,
                pagination=PaginationMetadataSchema(
                    page_number=result.page_number,
                    num_pages=result.num_pages,
                    has_previous=result.has_previous,
                    has_next=result.has_next,
                    total_results=result.total_results,
                    per_page=getattr(result, "per_page", len(result.results)),
                ),
            )

        # If it's a list, assume it's paginated data
        if isinstance(result, list):
            return create_paginated_response(
                data=result,
                pagination=PaginationMetadataSchema(
                    page_number=1,
                    num_pages=1,
                    has_previous=False,
                    has_next=False,
                    total_results=len(result),
                    per_page=len(result),
                ),
            )

        return create_success_response(data=result)

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        result = func(*args, **kwargs)

        if isinstance(result, PaginatedResponseSchema):
            return result

        if isinstance(result, BasePaginationSchema):
            return create_paginated_response(
                data=result.results,
                pagination=PaginationMetadataSchema(
                    page_number=result.page_number,
                    num_pages=result.num_pages,
                    has_previous=result.has_previous,
                    has_next=result.has_next,
                    total_results=result.total_results,
                    per_page=getattr(result, "per_page", len(result.results)),
                ),
            )

        # If it's a list, assume it's paginated data
        if isinstance(result, list):
            return create_paginated_response(
                data=result,
                pagination=PaginationMetadataSchema(
                    page_number=1,
                    num_pages=1,
                    has_previous=False,
                    has_next=False,
                    total_results=len(result),
                    per_page=len(result),
                ),
            )

        return create_success_response(data=result)

    # Check if the function is async and return appropriate wrapper
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def create_api_response(
    data: Any,
    message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    is_paginated: bool = False,
) -> SuccessResponseSchema | PaginatedResponseSchema:
    """Create a standardized API response."""
    if is_paginated and isinstance(data, BasePaginationSchema):
        return create_paginated_response(
            data=data.results,
            pagination=PaginationMetadataSchema(
                page_number=data.page_number,
                num_pages=data.num_pages,
                has_previous=data.has_previous,
                has_next=data.has_next,
                total_results=data.total_results,
                per_page=getattr(data, "per_page", len(data.results)),
            ),
            metadata=metadata,
        )

    return create_success_response(data=data, message=message, metadata=metadata)


def add_request_id_to_metadata(
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Add request ID to metadata for tracking."""
    if metadata is None:
        metadata = {}

    metadata["request_id"] = str(uuid.uuid4())
    return metadata


def create_list_response(
    items: List[Any],
    message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> SuccessResponseSchema:
    """Create a standardized response for list data."""
    return create_success_response(data=items, message=message, metadata=metadata)


def create_single_item_response(
    item: Any, message: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None
) -> SuccessResponseSchema:
    """Create a standardized response for single item data."""
    return create_success_response(data=item, message=message, metadata=metadata)


def create_empty_response(
    message: str = "No data found", metadata: Optional[Dict[str, Any]] = None
) -> SuccessResponseSchema:
    """Create a standardized response for empty results."""
    return create_success_response(data=[], message=message, metadata=metadata)
