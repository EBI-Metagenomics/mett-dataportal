"""Schemas for gene fitness correlation API endpoints."""

from typing import Optional, List, Dict, Any

from ninja import Schema

from dataportal.schema.base_schemas import BasePaginationSchema


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


class FitnessCorrelationSearchPaginationSchema(BasePaginationSchema):
    """Pagination schema for fitness correlation search results."""

    results: List[Dict[str, Any]]
