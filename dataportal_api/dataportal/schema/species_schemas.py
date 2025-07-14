from typing import Optional

from pydantic import BaseModel, Field
from pydantic import ConfigDict

from dataportal.utils.constants import (
    DEFAULT_PER_PAGE_CNT,
    DEFAULT_SORT,
    STRAIN_FIELD_ISOLATE_NAME,
)


class GenomesBySpeciesQuerySchema(BaseModel):
    """Schema for retrieving genomes by species with pagination and sorting."""
    page: int = Field(1, description="Page number to retrieve.")
    per_page: int = Field(DEFAULT_PER_PAGE_CNT, description="Number of genomes to return per page.")
    sortField: Optional[str] = Field(STRAIN_FIELD_ISOLATE_NAME, description="Field to sort results by.")
    sortOrder: Optional[str] = Field(DEFAULT_SORT, description="Sort order: 'asc' or 'desc'.")


class SearchGenomesBySpeciesQuerySchema(BaseModel):
    """Schema for searching genomes by species and query string with pagination and sorting."""
    query: Optional[str] = Field(None, description="Free-text search term for genome names or metadata. If not provided, returns all genomes for the species.")
    page: int = Field(1, description="Page number to retrieve.")
    per_page: int = Field(DEFAULT_PER_PAGE_CNT, description="Number of genomes to return per page.")
    sortField: Optional[str] = Field(STRAIN_FIELD_ISOLATE_NAME, description="Field to sort results by.")
    sortOrder: Optional[str] = Field(DEFAULT_SORT, description="Sort order: 'asc' or 'desc'.")


class SpeciesSchema(BaseModel):
    scientific_name: str
    common_name: str
    acronym: str
    taxonomy_id: int

    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "SpeciesSchema",
]
