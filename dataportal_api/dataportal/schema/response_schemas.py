from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

from dataportal.examples.response_examples import (
    PAGINATION_METADATA_EXAMPLE,
    SPECIES_PAGINATED_RESPONSE_EXAMPLE,
)


class ResponseStatus(str, Enum):
    """Standard response status values."""

    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


class ErrorCode(str, Enum):
    """Standard error codes for consistent error handling."""

    # General errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # Resource not found errors
    GENE_NOT_FOUND = "GENE_NOT_FOUND"
    GENOME_NOT_FOUND = "GENOME_NOT_FOUND"
    SPECIES_NOT_FOUND = "SPECIES_NOT_FOUND"
    CONTIG_NOT_FOUND = "CONTIG_NOT_FOUND"

    # Validation errors
    INVALID_GENOME_ID = "INVALID_GENOME_ID"
    INVALID_LOCUS_TAG = "INVALID_LOCUS_TAG"
    INVALID_SPECIES_ACRONYM = "INVALID_SPECIES_ACRONYM"
    INVALID_PAGINATION_PARAMS = "INVALID_PAGINATION_PARAMS"

    # Service errors
    ELASTICSEARCH_ERROR = "ELASTICSEARCH_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"

    # Authentication/Authorization errors
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INVALID_API_KEY = "INVALID_API_KEY"


class BaseResponseSchema(BaseModel):
    """Base response schema with common fields."""

    status: ResponseStatus = Field(..., description="Response status (success, error, warning)")
    message: Optional[str] = Field(None, description="Human-readable message")
    timestamp: str = Field(..., description="ISO 8601 timestamp of the response")

    model_config = ConfigDict(from_attributes=True)


class SuccessResponseSchema(BaseResponseSchema):
    """Standard success response schema."""

    status: ResponseStatus = Field(ResponseStatus.SUCCESS, description="Response status")
    data: Any = Field(..., description="Response data")


class ErrorDetailSchema(BaseModel):
    """Schema for detailed error information."""

    field: Optional[str] = Field(None, description="Field that caused the error")
    value: Optional[Any] = Field(None, description="Value that caused the error")
    message: str = Field(..., description="Specific error message for this field")

    model_config = ConfigDict(from_attributes=True)


class ErrorResponseSchema(BaseResponseSchema):
    """Standard error response schema."""

    status: ResponseStatus = Field(ResponseStatus.ERROR, description="Response status")
    error_code: ErrorCode = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[List[ErrorDetailSchema]] = Field(
        None, description="Detailed error information"
    )
    request_id: Optional[str] = Field(None, description="Unique request identifier for tracking")

    model_config = ConfigDict(from_attributes=True)


class PaginationMetadataSchema(BaseModel):
    """Enhanced pagination metadata."""

    page_number: int = Field(..., description="Current page number")
    num_pages: int = Field(..., description="Total number of pages")
    has_previous: bool = Field(..., description="Whether there is a previous page")
    has_next: bool = Field(..., description="Whether there is a next page")
    total_results: int = Field(..., description="Total number of results")
    per_page: int = Field(..., description="Number of items per page")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": PAGINATION_METADATA_EXAMPLE},
    )


class PaginatedResponseSchema(BaseResponseSchema):
    """Standard paginated response schema."""

    status: ResponseStatus = Field(ResponseStatus.SUCCESS, description="Response status")
    data: List[Any] = Field(..., description="List of response items")
    pagination: PaginationMetadataSchema = Field(..., description="Pagination metadata")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": SPECIES_PAGINATED_RESPONSE_EXAMPLE},
    )


class HealthResponseSchema(BaseResponseSchema):
    """Health check response schema."""

    status: ResponseStatus = Field(..., description="Response status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    uptime: Optional[float] = Field(None, description="Service uptime in seconds")
    dependencies: Optional[Dict[str, str]] = Field(None, description="Dependency status")


# Response wrapper functions for consistent formatting
def create_success_response(
    data: Any, message: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None
) -> SuccessResponseSchema:
    """Create a standardized success response.

    Note: metadata parameter is kept for backward compatibility but not used in schema.
    """
    from datetime import datetime

    return SuccessResponseSchema(
        status=ResponseStatus.SUCCESS,
        message=message,
        data=data,
        timestamp=datetime.utcnow().isoformat() + "Z",
    )


def create_error_response(
    error_code: ErrorCode,
    message: str,
    details: Optional[List[ErrorDetailSchema]] = None,
    request_id: Optional[str] = None,
) -> ErrorResponseSchema:
    """Create a standardized error response."""
    from datetime import datetime

    return ErrorResponseSchema(
        status=ResponseStatus.ERROR,
        error_code=error_code,
        message=message,
        details=details,
        request_id=request_id,
        timestamp=datetime.utcnow().isoformat() + "Z",
    )


def create_paginated_response(
    data: List[Any],
    pagination: PaginationMetadataSchema,
    metadata: Optional[Dict[str, Any]] = None,
) -> PaginatedResponseSchema:
    """Create a standardized paginated response.

    Note: metadata parameter is kept for backward compatibility but not used in schema.
    """
    from datetime import datetime

    return PaginatedResponseSchema(
        status=ResponseStatus.SUCCESS,
        data=data,
        pagination=pagination,
        timestamp=datetime.utcnow().isoformat() + "Z",
    )


__all__ = [
    "ResponseStatus",
    "ErrorCode",
    "BaseResponseSchema",
    "SuccessResponseSchema",
    "ErrorResponseSchema",
    "ErrorDetailSchema",
    "PaginationMetadataSchema",
    "PaginatedResponseSchema",
    "HealthResponseSchema",
    "create_success_response",
    "create_error_response",
    "create_paginated_response",
]
