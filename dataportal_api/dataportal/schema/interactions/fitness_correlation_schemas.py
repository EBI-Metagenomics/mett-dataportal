"""Schemas for gene fitness correlation API endpoints."""

from typing import Optional
from ninja import Schema


class GeneCorrelationQuerySchema(Schema):
    """Schema for gene correlation query parameters."""
    locus_tag: str
    species_acronym: Optional[str] = None
    min_correlation: Optional[float] = None
    max_results: int = 100


class GenePairCorrelationQuerySchema(Schema):
    """Schema for querying correlation between two genes."""
    locus_tag_a: str
    locus_tag_b: str
    species_acronym: Optional[str] = None


class TopCorrelationsQuerySchema(Schema):
    """Schema for top correlations query."""
    species_acronym: Optional[str] = None
    correlation_strength: Optional[str] = None
    limit: int = 100


class CorrelationSearchQuerySchema(Schema):
    """Schema for correlation search."""
    query: str
    species_acronym: Optional[str] = None
    page: int = 1
    per_page: int = 20

