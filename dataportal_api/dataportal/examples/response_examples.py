"""OpenAPI examples for shared response envelopes."""

from dataportal.examples.genome_examples import GENOME_RESPONSE_EXAMPLE
from dataportal.examples.gene_examples import GENE_RESPONSE_EXAMPLE
from dataportal.examples.species_examples import SPECIES_COLLECTION_EXAMPLE

PAGINATION_METADATA_EXAMPLE = {
    "page_number": 1,
    "num_pages": 12,
    "has_previous": False,
    "has_next": True,
    "total_results": 200,
    "per_page": 20,
}

SPECIES_PAGINATED_RESPONSE_EXAMPLE = {
    "status": "success",
    "message": "Genomes retrieved for species BU",
    "timestamp": "2024-05-03T10:15:00Z",
    "data": SPECIES_COLLECTION_EXAMPLE,
    "pagination": PAGINATION_METADATA_EXAMPLE,
}

GENOME_PAGINATED_RESPONSE_EXAMPLE = {
    "status": "success",
    "message": "Genome results",
    "timestamp": "2024-05-03T11:25:00Z",
    "data": [GENOME_RESPONSE_EXAMPLE],
    "pagination": PAGINATION_METADATA_EXAMPLE,
}

GENE_PAGINATED_RESPONSE_EXAMPLE = {
    "status": "success",
    "message": "Gene results",
    "timestamp": "2024-05-03T11:30:00Z",
    "data": [GENE_RESPONSE_EXAMPLE],
    "pagination": PAGINATION_METADATA_EXAMPLE,
}


__all__ = [
    "PAGINATION_METADATA_EXAMPLE",
    "SPECIES_PAGINATED_RESPONSE_EXAMPLE",
    "GENOME_PAGINATED_RESPONSE_EXAMPLE",
    "GENE_PAGINATED_RESPONSE_EXAMPLE",
]
