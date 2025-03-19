class NotFoundError(Exception):
    def __init__(self, message: str):
        self.log_message = f"NotFoundError occurred: {message}"
        super().__init__(message)


class ValidationError(Exception):
    def __init__(self, message: str):
        self.log_message = f"ValidationError occurred: {message}"
        super().__init__(message)


class ServiceError(Exception):
    def __init__(self, message: str):
        self.log_message = f"ServiceError occurred: {message}"
        super().__init__(message)


class GeneNotFoundError(ServiceError):
    def __init__(self, locus_tag: str, message: str = "Gene not found"):
        self.locus_tag = locus_tag
        self.message = f"{message}: {locus_tag}"
        super().__init__(self.message)


class GenomeNotFoundError(ServiceError):
    def __init__(self, message: str = "Genome not found"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message


class InvalidGenomeIdError(ServiceError):
    def __init__(self, genome_ids: str, message: str = "Invalid Genome Ids Provided."):
        self.genome_ids = genome_ids
        self.message = f"{message}: {genome_ids}"
        super().__init__(self.message)
