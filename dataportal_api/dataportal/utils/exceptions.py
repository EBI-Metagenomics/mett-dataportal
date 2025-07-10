from dataportal.schema.response_schemas import ErrorCode


class NotFoundError(Exception):
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.GENE_NOT_FOUND):
        self.log_message = f"NotFoundError occurred: {message}"
        self.error_code = error_code
        super().__init__(message)


class ValidationError(Exception):
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.VALIDATION_ERROR):
        self.log_message = f"ValidationError occurred: {message}"
        self.error_code = error_code
        super().__init__(message)


class ServiceError(Exception):
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.INTERNAL_SERVER_ERROR):
        self.log_message = f"ServiceError occurred: {message}"
        self.error_code = error_code
        super().__init__(message)


class GeneNotFoundError(ServiceError):
    def __init__(self, locus_tag: str, message: str = "Gene not found"):
        self.locus_tag = locus_tag
        self.message = f"{message}: {locus_tag}"
        super().__init__(self.message, ErrorCode.GENE_NOT_FOUND)


class GenomeNotFoundError(ServiceError):
    def __init__(self, isolate_name: str = None, message: str = "Genome not found"):
        self.isolate_name = isolate_name
        self.message = f"{message}: {isolate_name}" if isolate_name else message
        super().__init__(self.message, ErrorCode.GENOME_NOT_FOUND)

    def __str__(self):
        return self.message


class InvalidGenomeIdError(ServiceError):
    def __init__(self, genome_ids: str, message: str = "Invalid Genome Ids Provided."):
        self.genome_ids = genome_ids
        self.message = f"{message}: {genome_ids}"
        super().__init__(self.message, ErrorCode.INVALID_GENOME_ID)


class SpeciesNotFoundError(ServiceError):
    def __init__(self, species_acronym: str = None, message: str = "Species not found"):
        self.species_acronym = species_acronym
        self.message = f"{message}: {species_acronym}" if species_acronym else message
        super().__init__(self.message, ErrorCode.SPECIES_NOT_FOUND)


class ElasticsearchError(ServiceError):
    def __init__(self, message: str = "Elasticsearch error occurred"):
        super().__init__(message, ErrorCode.ELASTICSEARCH_ERROR)


class DatabaseError(ServiceError):
    def __init__(self, message: str = "Database error occurred"):
        super().__init__(message, ErrorCode.DATABASE_ERROR)


class ExternalServiceError(ServiceError):
    def __init__(self, message: str = "External service error occurred"):
        super().__init__(message, ErrorCode.EXTERNAL_SERVICE_ERROR)


class RateLimitError(ServiceError):
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, ErrorCode.RATE_LIMIT_EXCEEDED)


class AuthenticationError(ServiceError):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, ErrorCode.UNAUTHORIZED)


class AuthorizationError(ServiceError):
    def __init__(self, message: str = "Access forbidden"):
        super().__init__(message, ErrorCode.FORBIDDEN)
