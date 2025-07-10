import json
import logging
import inspect
import uuid
from typing import List, Optional, Dict, Any
from django.http import JsonResponse
from ninja.errors import HttpError

from dataportal.schema.response_schemas import (
    ErrorCode, 
    ErrorResponseSchema, 
    ErrorDetailSchema,
    create_error_response
)

logger = logging.getLogger(__name__)


def raise_http_error(
    status_code: int, 
    message: str, 
    error_code: Optional[ErrorCode] = None,
    details: Optional[List[ErrorDetailSchema]] = None,
    request_id: Optional[str] = None
):
    """Raise an HTTP error with standardized error response."""
    frame = inspect.currentframe().f_back
    function_name = frame.f_code.co_name if frame else "Unknown"

    cls_name = None
    if "self" in frame.f_locals:
        cls_name = (
            frame.f_locals["self"].__class__.__name__
            if "self" in frame.f_locals
            else "Unknown"
        )

    # Generate request ID if not provided
    if not request_id:
        request_id = str(uuid.uuid4())

    # Map status codes to error codes if not provided
    if not error_code:
        error_code = _map_status_code_to_error_code(status_code)

    logger.error(
        f"HTTP Error {status_code} ({error_code}): {message}. "
        f"Request ID: {request_id}. "
        f"Originated from: {cls_name + '.' if cls_name else ''}{function_name}"
    )

    # Create standardized error response
    error_response = create_error_response(
        error_code=error_code,
        message=message,
        details=details,
        request_id=request_id
    )

    # Raise HttpError with a JSON string message
    raise HttpError(status_code, json.dumps(error_response.model_dump()))


def raise_validation_error(
    message: str,
    details: Optional[List[ErrorDetailSchema]] = None,
    request_id: Optional[str] = None
):
    """Raise a validation error (400 Bad Request)."""
    raise_http_error(
        status_code=400,
        message=message,
        error_code=ErrorCode.VALIDATION_ERROR,
        details=details,
        request_id=request_id
    )


def raise_not_found_error(
    message: str,
    error_code: ErrorCode = ErrorCode.GENE_NOT_FOUND,
    request_id: Optional[str] = None
):
    """Raise a not found error (404 Not Found)."""
    raise_http_error(
        status_code=404,
        message=message,
        error_code=error_code,
        request_id=request_id
    )


def raise_internal_server_error(
    message: str = "An internal server error occurred",
    request_id: Optional[str] = None
):
    """Raise an internal server error (500 Internal Server Error)."""
    raise_http_error(
        status_code=500,
        message=message,
        error_code=ErrorCode.INTERNAL_SERVER_ERROR,
        request_id=request_id
    )


def raise_service_unavailable_error(
    message: str = "Service temporarily unavailable",
    request_id: Optional[str] = None
):
    """Raise a service unavailable error (503 Service Unavailable)."""
    raise_http_error(
        status_code=503,
        message=message,
        error_code=ErrorCode.SERVICE_UNAVAILABLE,
        request_id=request_id
    )


def raise_elasticsearch_error(
    message: str,
    request_id: Optional[str] = None
):
    """Raise an Elasticsearch-specific error."""
    raise_http_error(
        status_code=500,
        message=message,
        error_code=ErrorCode.ELASTICSEARCH_ERROR,
        request_id=request_id
    )


def raise_rate_limit_error(
    message: str = "Rate limit exceeded",
    request_id: Optional[str] = None
):
    """Raise a rate limit error (429 Too Many Requests)."""
    raise_http_error(
        status_code=429,
        message=message,
        error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
        request_id=request_id
    )


def create_validation_error_details(
    field_errors: Dict[str, str]
) -> List[ErrorDetailSchema]:
    """Create validation error details from field errors."""
    details = []
    for field, error_message in field_errors.items():
        details.append(ErrorDetailSchema(
            field=field,
            message=error_message
        ))
    return details


def _map_status_code_to_error_code(status_code: int) -> ErrorCode:
    """Map HTTP status codes to error codes."""
    status_code_mapping = {
        400: ErrorCode.VALIDATION_ERROR,
        401: ErrorCode.UNAUTHORIZED,
        403: ErrorCode.FORBIDDEN,
        404: ErrorCode.GENE_NOT_FOUND,
        422: ErrorCode.VALIDATION_ERROR,
        429: ErrorCode.RATE_LIMIT_EXCEEDED,
        500: ErrorCode.INTERNAL_SERVER_ERROR,
        503: ErrorCode.SERVICE_UNAVAILABLE,
    }
    return status_code_mapping.get(status_code, ErrorCode.INTERNAL_SERVER_ERROR)


def raise_exception(message: str):
    """Legacy function for backward compatibility."""
    frame = inspect.currentframe().f_back
    function_name = frame.f_code.co_name if frame else "Unknown"

    cls_name = None
    if "self" in frame.f_locals:
        cls_name = (
            frame.f_locals["self"].__class__.__name__
            if "self" in frame.f_locals
            else "Unknown"
        )

    logger.error(
        f"Exception: {message}. "
        f"Originated from: {cls_name + '.' if cls_name else ''}{function_name}"
    )

    raise Exception(message)
