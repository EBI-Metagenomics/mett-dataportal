"""Gene/protein interaction API endpoints."""

from dataportal.api.interactions.ppi_endpoints import ppi_router
from dataportal.api.interactions.ttp_endpoints import ttp_router
from dataportal.api.interactions.fitness_correlation_endpoints import fitness_correlation_router

__all__ = [
    "ppi_router",
    "ttp_router",
    "fitness_correlation_router",
]

