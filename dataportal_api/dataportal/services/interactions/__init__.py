"""Gene/protein interaction services."""

from dataportal.services.interactions.ppi_service import PPIService
from dataportal.services.interactions.ttp_service import TTPService
from dataportal.services.interactions.fitness_correlation_service import FitnessCorrelationService
from dataportal.services.interactions.ortholog_service import OrthologService
from dataportal.services.interactions.operon_service import OperonService

__all__ = [
    "PPIService",
    "TTPService",
    "FitnessCorrelationService",
    "OrthologService",
    "OperonService",
]

