import traceback
from typing import Any

from dataportal.schema.response_schemas import ErrorCode


class BaseServiceException(Exception):
    """Base exception class for all service exceptions."""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.INTERNAL_SERVER_ERROR,
        context: dict[str, Any] | None = None,
        request_id: str | None = None,
    ):
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.request_id = request_id
        self.traceback = traceback.format_exc()

        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for logging/monitoring."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "context": self.context,
            "request_id": self.request_id,
            "traceback": self.traceback,
        }


class NotFoundError(BaseServiceException):
    """Base class for not found errors."""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.GENE_NOT_FOUND,
        context: dict[str, Any] | None = None,
        request_id: str | None = None,
    ):
        super().__init__(message, error_code, context, request_id)


class ValidationError(BaseServiceException):
    """Validation error with field-specific details."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: Any | None = None,
        error_code: ErrorCode = ErrorCode.VALIDATION_ERROR,
        context: dict[str, Any] | None = None,
        request_id: str | None = None,
    ):
        if field:
            context = context or {}
            context.update({"field": field, "value": value})

        super().__init__(message, error_code, context, request_id)


class ServiceError(BaseServiceException):
    """General service error."""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.INTERNAL_SERVER_ERROR,
        context: dict[str, Any] | None = None,
        request_id: str | None = None,
    ):
        super().__init__(message, error_code, context, request_id)


class GeneNotFoundError(NotFoundError):
    """Gene not found error."""

    def __init__(
        self,
        locus_tag: str,
        message: str = "Gene not found",
        context: dict[str, Any] | None = None,
        request_id: str | None = None,
    ):
        context = context or {}
        context.update({"locus_tag": locus_tag})
        super().__init__(
            f"{message}: {locus_tag}", ErrorCode.GENE_NOT_FOUND, context, request_id
        )


class GenomeNotFoundError(NotFoundError):
    """Genome not found error."""

    def __init__(
        self,
        isolate_name: str | None = None,
        message: str = "Genome not found",
        context: dict[str, Any] | None = None,
        request_id: str | None = None,
    ):
        context = context or {}
        if isolate_name:
            context.update({"isolate_name": isolate_name})
            message = f"{message}: {isolate_name}"

        super().__init__(message, ErrorCode.GENOME_NOT_FOUND, context, request_id)


class InvalidGenomeIdError(ValidationError):
    """Invalid genome ID error."""

    def __init__(
        self,
        genome_ids: str,
        message: str = "Invalid Genome Ids Provided",
        context: dict[str, Any] | None = None,
        request_id: str | None = None,
    ):
        context = context or {}
        context.update({"genome_ids": genome_ids})
        super().__init__(
            f"{message}: {genome_ids}",
            field="genome_ids",
            value=genome_ids,
            error_code=ErrorCode.INVALID_GENOME_ID,
            context=context,
            request_id=request_id,
        )


class SpeciesNotFoundError(NotFoundError):
    """Species not found error."""

    def __init__(
        self,
        species_acronym: str | None = None,
        message: str = "Species not found",
        context: dict[str, Any] | None = None,
        request_id: str | None = None,
    ):
        context = context or {}
        if species_acronym:
            context.update({"species_acronym": species_acronym})
            message = f"{message}: {species_acronym}"

        super().__init__(message, ErrorCode.SPECIES_NOT_FOUND, context, request_id)


class ElasticsearchError(ServiceError):
    """Elasticsearch-specific error."""

    def __init__(
        self,
        message: str = "Elasticsearch error occurred",
        operation: str | None = None,
        query: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
        request_id: str | None = None,
    ):
        context = context or {}
        if operation:
            context.update({"operation": operation})
        if query:
            context.update({"query": query})

        super().__init__(message, ErrorCode.ELASTICSEARCH_ERROR, context, request_id)


class DatabaseError(ServiceError):
    """Database-specific error."""

    def __init__(
        self,
        message: str = "Database error occurred",
        operation: str | None = None,
        context: dict[str, Any] | None = None,
        request_id: str | None = None,
    ):
        context = context or {}
        if operation:
            context.update({"operation": operation})

        super().__init__(message, ErrorCode.DATABASE_ERROR, context, request_id)


class ExternalServiceError(ServiceError):
    """External service error."""

    def __init__(
        self,
        message: str = "External service error occurred",
        service_name: str | None = None,
        status_code: int | None = None,
        context: dict[str, Any] | None = None,
        request_id: str | None = None,
    ):
        context = context or {}
        if service_name:
            context.update({"service_name": service_name})
        if status_code:
            context.update({"status_code": status_code})

        super().__init__(message, ErrorCode.EXTERNAL_SERVICE_ERROR, context, request_id)


class RateLimitError(ServiceError):
    """Rate limit exceeded error."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        limit: int | None = None,
        window: int | None = None,
        context: dict[str, Any] | None = None,
        request_id: str | None = None,
    ):
        context = context or {}
        if limit:
            context.update({"limit": limit})
        if window:
            context.update({"window": window})

        super().__init__(message, ErrorCode.RATE_LIMIT_EXCEEDED, context, request_id)


class AuthenticationError(ServiceError):
    """Authentication error."""

    def __init__(
        self,
        message: str = "Authentication failed",
        auth_method: str | None = None,
        context: dict[str, Any] | None = None,
        request_id: str | None = None,
    ):
        context = context or {}
        if auth_method:
            context.update({"auth_method": auth_method})

        super().__init__(message, ErrorCode.UNAUTHORIZED, context, request_id)


class AuthorizationError(ServiceError):
    """Authorization error."""

    def __init__(
        self,
        message: str = "Access forbidden",
        required_permissions: list | None = None,
        user_permissions: list | None = None,
        context: dict[str, Any] | None = None,
        request_id: str | None = None,
    ):
        context = context or {}
        if required_permissions:
            context.update({"required_permissions": required_permissions})
        if user_permissions:
            context.update({"user_permissions": user_permissions})

        super().__init__(message, ErrorCode.FORBIDDEN, context, request_id)
