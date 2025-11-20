import asyncio
import uuid
from functools import wraps
from typing import Any, Dict, List, Optional, Sequence

from django.http import HttpResponse

from dataportal.schema.base_schemas import BasePaginationSchema
from dataportal.schema.response_schemas import (
    PaginatedResponseSchema,
    PaginationMetadataSchema,
    ResponseFormat,
    SuccessResponseSchema,
    create_paginated_response,
    create_success_response,
    normalize_response_format,
)
from dataportal.utils.serialization import serialize_to_tsv


def _extract_response_format(args: Sequence[Any], kwargs: Dict[str, Any]) -> ResponseFormat:
    """Determine desired response format from kwargs or the incoming request."""

    if "format" in kwargs:
        return normalize_response_format(kwargs.get("format"))

    if args:
        request = args[0]
        try:
            query_format = getattr(request, "GET", {}).get("format")
            if query_format:
                return normalize_response_format(query_format)
        except Exception:
            pass

    return ResponseFormat.JSON


def _finalize_formatted_response(
    response_obj: Any,
    response_format: ResponseFormat,
) -> Any:
    """Convert standardized responses to alternate formats when requested."""

    if response_format != ResponseFormat.TSV:
        return response_obj

    if isinstance(response_obj, HttpResponse):
        return response_obj

    if isinstance(response_obj, SuccessResponseSchema):
        payload = response_obj.data
    elif isinstance(response_obj, PaginatedResponseSchema):
        payload = response_obj.data
    else:
        payload = response_obj

    tsv_payload = serialize_to_tsv(payload)
    response = HttpResponse(
        tsv_payload,
        content_type="text/tab-separated-values",
    )
    response["Content-Disposition"] = 'attachment; filename="response.tsv"'
    return response


def wrap_success_response(func):
    """Decorator to wrap function responses in standardized success format."""

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        response_format = _extract_response_format(args, kwargs)
        result = await func(*args, **kwargs)

        # If result is already a response schema, return as is
        if isinstance(result, (SuccessResponseSchema, PaginatedResponseSchema)):
            return _finalize_formatted_response(result, response_format)

        if isinstance(result, HttpResponse):
            return result

        # If result is a pagination schema, convert to paginated response
        if isinstance(result, BasePaginationSchema):
            return _finalize_formatted_response(
                create_paginated_response(
                    data=result.results,
                    pagination=PaginationMetadataSchema(
                        page_number=result.page_number,
                        num_pages=result.num_pages,
                        has_previous=result.has_previous,
                        has_next=result.has_next,
                        total_results=result.total_results,
                        per_page=getattr(result, "per_page", len(result.results)),
                    ),
                ),
                response_format,
            )

        # Otherwise, wrap in success response
        return _finalize_formatted_response(
            create_success_response(data=result),
            response_format,
        )

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        response_format = _extract_response_format(args, kwargs)
        result = func(*args, **kwargs)

        # If result is already a response schema, return as is
        if isinstance(result, (SuccessResponseSchema, PaginatedResponseSchema)):
            return _finalize_formatted_response(result, response_format)

        if isinstance(result, HttpResponse):
            return result

        # If result is a pagination schema, convert to paginated response
        if isinstance(result, BasePaginationSchema):
            return _finalize_formatted_response(
                create_paginated_response(
                    data=result.results,
                    pagination=PaginationMetadataSchema(
                        page_number=result.page_number,
                        num_pages=result.num_pages,
                        has_previous=result.has_previous,
                        has_next=result.has_next,
                        total_results=result.total_results,
                        per_page=getattr(result, "per_page", len(result.results)),
                    ),
                ),
                response_format,
            )

        # Otherwise, wrap in success response
        return _finalize_formatted_response(
            create_success_response(data=result),
            response_format,
        )

    # Check if the function is async and return appropriate wrapper
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def wrap_paginated_response(func):
    """Decorator specifically for paginated responses."""

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        response_format = _extract_response_format(args, kwargs)
        result = await func(*args, **kwargs)

        if isinstance(result, PaginatedResponseSchema):
            return _finalize_formatted_response(result, response_format)

        if isinstance(result, HttpResponse):
            return result

        if isinstance(result, BasePaginationSchema):
            return _finalize_formatted_response(
                create_paginated_response(
                    data=result.results,
                    pagination=PaginationMetadataSchema(
                        page_number=result.page_number,
                        num_pages=result.num_pages,
                        has_previous=result.has_previous,
                        has_next=result.has_next,
                        total_results=result.total_results,
                        per_page=getattr(result, "per_page", len(result.results)),
                    ),
                ),
                response_format,
            )

        # If it's a list, assume it's paginated data
        if isinstance(result, list):
            return _finalize_formatted_response(
                create_paginated_response(
                    data=result,
                    pagination=PaginationMetadataSchema(
                        page_number=1,
                        num_pages=1,
                        has_previous=False,
                        has_next=False,
                        total_results=len(result),
                        per_page=len(result),
                    ),
                ),
                response_format,
            )

        return _finalize_formatted_response(
            create_success_response(data=result),
            response_format,
        )

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        response_format = _extract_response_format(args, kwargs)
        result = func(*args, **kwargs)

        if isinstance(result, PaginatedResponseSchema):
            return _finalize_formatted_response(result, response_format)

        if isinstance(result, HttpResponse):
            return result

        if isinstance(result, BasePaginationSchema):
            return _finalize_formatted_response(
                create_paginated_response(
                    data=result.results,
                    pagination=PaginationMetadataSchema(
                        page_number=result.page_number,
                        num_pages=result.num_pages,
                        has_previous=result.has_previous,
                        has_next=result.has_next,
                        total_results=result.total_results,
                        per_page=getattr(result, "per_page", len(result.results)),
                    ),
                ),
                response_format,
            )

        # If it's a list, assume it's paginated data
        if isinstance(result, list):
            return _finalize_formatted_response(
                create_paginated_response(
                    data=result,
                    pagination=PaginationMetadataSchema(
                        page_number=1,
                        num_pages=1,
                        has_previous=False,
                        has_next=False,
                        total_results=len(result),
                        per_page=len(result),
                    ),
                ),
                response_format,
            )

        return _finalize_formatted_response(
            create_success_response(data=result),
            response_format,
        )

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
    response_format: ResponseFormat = ResponseFormat.JSON,
) -> SuccessResponseSchema | PaginatedResponseSchema | HttpResponse:
    """Create a standardized API response."""
    if is_paginated and isinstance(data, BasePaginationSchema):
        wrapped = create_paginated_response(
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
    else:
        wrapped = create_success_response(data=data, message=message, metadata=metadata)

    return _finalize_formatted_response(wrapped, response_format)


def add_request_id_to_metadata(metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Add request ID to metadata for tracking."""
    if metadata is None:
        metadata = {}

    metadata["request_id"] = str(uuid.uuid4())
    return metadata


def create_list_response(
    items: List[Any],
    message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    response_format: ResponseFormat = ResponseFormat.JSON,
) -> SuccessResponseSchema | HttpResponse:
    """Create a standardized response for list data."""
    return _finalize_formatted_response(
        create_success_response(data=items, message=message, metadata=metadata),
        response_format,
    )


def create_single_item_response(
    item: Any,
    message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    response_format: ResponseFormat = ResponseFormat.JSON,
) -> SuccessResponseSchema | HttpResponse:
    """Create a standardized response for single item data."""
    return _finalize_formatted_response(
        create_success_response(data=item, message=message, metadata=metadata),
        response_format,
    )


def create_empty_response(
    message: str = "No data found",
    metadata: Optional[Dict[str, Any]] = None,
    response_format: ResponseFormat = ResponseFormat.JSON,
) -> SuccessResponseSchema | HttpResponse:
    """Create a standardized response for empty results."""
    return _finalize_formatted_response(
        create_success_response(data=[], message=message, metadata=metadata),
        response_format,
    )
