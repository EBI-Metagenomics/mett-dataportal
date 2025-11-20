"""
Elasticsearch document models for the METT Data Portal.

This module provides a clean interface to all document models by importing
them from their respective domain-specific modules.
"""

from .base import (
    edge_ngram_tokenizer,
    autocomplete_analyzer,
    lowercase_normalizer,
    canonical_pair,
    build_pair_id,
)
from .species import SpeciesDocument
from .strains import StrainDocument
from .features import FeatureDocument
from .interactions import ProteinProteinDocument
from .operons import OperonDocument
from .orthologs import OrthologDocument
from .fitness_correlation import GeneFitnessCorrelationDocument
from .role import Role
from .api_token import APIToken

__all__ = [
    # Base utilities
    "edge_ngram_tokenizer",
    "autocomplete_analyzer", 
    "lowercase_normalizer",
    "canonical_pair",
    "build_pair_id",
    # Document models
    "SpeciesDocument",
    "StrainDocument", 
    "FeatureDocument",
    "ProteinProteinDocument",
    "OperonDocument",
    "OrthologDocument",
    "GeneFitnessCorrelationDocument",
    # Database models
    "Role",
    "APIToken",
]
