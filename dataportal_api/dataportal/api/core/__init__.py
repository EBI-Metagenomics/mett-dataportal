"""Core API endpoints for genomic entities."""

from dataportal.api.core.gene_endpoints import gene_router
from dataportal.api.core.genome_endpoints import genome_router
from dataportal.api.core.species_endpoints import species_router
from dataportal.api.core.metadata_endpoints import metadata_router
from dataportal.api.core.health_endpoints import health_router

__all__ = [
    "gene_router",
    "genome_router",
    "species_router",
    "metadata_router",
    "health_router",
]

