"""OpenAPI examples for shared response envelopes."""

from dataportal.examples.genome_examples import GENOME_RESPONSE_EXAMPLE

PAGINATION_METADATA_EXAMPLE = {
    "page_number": 1,
    "num_pages": 12,
    "has_previous": False,
    "has_next": True,
    "total_results": 236,
    "per_page": 25,
}

SPECIES_PAGINATED_RESPONSE_EXAMPLE = {
    "status": "success",
    "message": "Genomes retrieved for species BU",
    "timestamp": "2024-05-03T10:15:00Z",
    "data": [GENOME_RESPONSE_EXAMPLE],
    "pagination": PAGINATION_METADATA_EXAMPLE,
}


__all__ = [
    "PAGINATION_METADATA_EXAMPLE",
    "SPECIES_PAGINATED_RESPONSE_EXAMPLE",
]
