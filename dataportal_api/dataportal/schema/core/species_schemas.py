from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field

from dataportal.examples.species_examples import (
    SPECIES_PRIMARY_EXAMPLE,
    SPECIES_GENOME_SEARCH_QUERY_EXAMPLE,
)
from dataportal.utils.constants import (
    DEFAULT_PAGE_SIZE,
    DEFAULT_SORT_DIRECTION,
    GENOME_FIELD_ISOLATE_NAME,
)


class SpeciesSchema(BaseModel):
    scientific_name: str
    common_name: str
    acronym: str
    taxonomy_id: int
    enabled: bool = Field(
        default=True, description="Whether the species is enabled and visible in API responses"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": SPECIES_PRIMARY_EXAMPLE},
    )


class SpeciesGenomeSearchQuerySchema(BaseModel):
    """Query parameters for genome lookups scoped to a species."""

    query: str = Field("", description="Search term to match against genome names or metadata.")
    page: int = Field(1, description="Page number to retrieve.")
    per_page: int = Field(DEFAULT_PAGE_SIZE, description="Number of genomes to return per page.")
    sortField: Optional[str] = Field(
        GENOME_FIELD_ISOLATE_NAME, description="Field to sort results by."
    )
    sortOrder: Optional[str] = Field(
        DEFAULT_SORT_DIRECTION, description="Sort order: 'asc' or 'desc'."
    )
    isolates: Optional[List[str]] = Field(
        None, description="Optional list of isolate names to filter."
    )

    model_config = ConfigDict(
        json_schema_extra={"example": SPECIES_GENOME_SEARCH_QUERY_EXAMPLE},
    )

    def to_genome_search_query(self, species_acronym: str):
        """Convert to the canonical genome search schema while injecting the species."""
        from dataportal.schema.core.genome_schemas import GenomeSearchQuerySchema

        payload = self.model_dump()
        payload["species_acronym"] = species_acronym
        return GenomeSearchQuerySchema(**payload)


__all__ = [
    "SpeciesSchema",
    "SpeciesGenomeSearchQuerySchema",
]
