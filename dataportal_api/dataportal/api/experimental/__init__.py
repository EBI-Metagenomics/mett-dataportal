"""Experimental data API endpoints."""

from dataportal.api.experimental.proteomics_endpoints import proteomics_router
from dataportal.api.experimental.essentiality_endpoints import essentiality_router
from dataportal.api.experimental.fitness_endpoints import fitness_router
from dataportal.api.experimental.mutant_growth_endpoints import mutant_growth_router
from dataportal.api.experimental.reactions_endpoints import reactions_router
from dataportal.api.experimental.drug_endpoints import drug_router

__all__ = [
    "proteomics_router",
    "essentiality_router",
    "fitness_router",
    "mutant_growth_router",
    "reactions_router",
    "drug_router",
]

