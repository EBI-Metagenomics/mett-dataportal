"""Reusable Swagger/OpenAPI examples for species-facing endpoints."""

SPECIES_PRIMARY_EXAMPLE = {
    "scientific_name": "Bacteroides uniformis",
    "common_name": "Bacteroides",
    "acronym": "BU",
    "taxonomy_id": 820,
}

SPECIES_SECONDARY_EXAMPLE = {
    "scientific_name": "Phocaeicola vulgatus",
    "common_name": "Bacteroides vulgatus",
    "acronym": "PV",
    "taxonomy_id": 821,
}

SPECIES_COLLECTION_EXAMPLE = [
    SPECIES_PRIMARY_EXAMPLE,
    SPECIES_SECONDARY_EXAMPLE,
]

SPECIES_GENOME_SEARCH_QUERY_EXAMPLE = {
    "query": "type strain",
    "page": 1,
    "per_page": 25,
    "sortField": "isolate_name",
    "sortOrder": "asc",
    "isolates": ["BU_ATCC8492", "PV_ATCC8482"],
}


__all__ = [
    "SPECIES_PRIMARY_EXAMPLE",
    "SPECIES_SECONDARY_EXAMPLE",
    "SPECIES_COLLECTION_EXAMPLE",
    "SPECIES_GENOME_SEARCH_QUERY_EXAMPLE",
]
