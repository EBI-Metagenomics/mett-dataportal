"""Gene/protein interaction services."""

from dataportal.services.interactions.ppi_service import PPIService
from dataportal.services.interactions.ttp_service import TTPService
from dataportal.services.interactions.fitness_correlation_service import FitnessCorrelationService

__all__ = [
    "PPIService",
    "TTPService",
    "FitnessCorrelationService",
]

