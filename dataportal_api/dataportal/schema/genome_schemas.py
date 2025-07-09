from pydantic import ConfigDict

from typing import Optional, List

from pydantic import BaseModel, Field
from pydantic import ConfigDict

from dataportal.schema.base_schemas import BasePaginationSchema
from dataportal.utils.constants import (
    DEFAULT_PER_PAGE_CNT,
    DEFAULT_SORT,
    STRAIN_FIELD_ISOLATE_NAME,
)


class GenomeAutocompleteQuerySchema(BaseModel):
    """Schema for genome autocomplete endpoint."""
    query: str = Field(..., description="Search term for isolate/genome name autocomplete.")
    limit: int = Field(DEFAULT_PER_PAGE_CNT, description="Maximum number of suggestions to return.")
    species_acronym: Optional[str] = Field(None,
                                           description="Optional species acronym (BU or PV) to filter suggestions.")


class GenomeSearchQuerySchema(BaseModel):
    """Schema for searching genomes using a free-text query with pagination and sorting."""
    query: str = Field(..., description="Search term to match against genome names or metadata.")
    page: int = Field(1, description="Page number to retrieve.")
    per_page: int = Field(DEFAULT_PER_PAGE_CNT, description="Number of genomes to return per page.")
    sortField: Optional[str] = Field(STRAIN_FIELD_ISOLATE_NAME, description="Field to sort results by.")
    sortOrder: Optional[str] = Field(DEFAULT_SORT, description="Sort order: 'asc' or 'desc'.")
    isolates: Optional[List[str]] = Field(None, description="Optional list of isolate names to filter.")
    species_acronym: Optional[str] = Field(None, description="Optional species acronym filter (BU, PV).")


class GenomesByIsolateNamesQuerySchema(BaseModel):
    """Schema for retrieving genomes by a comma-separated list of isolate names."""
    isolates: str = Field(
        ...,
        description="Comma-separated isolate names (e.g., 'BU_61,BU_909,BU_ATCC8492')."
    )


class GetAllGenomesQuerySchema(BaseModel):
    """Schema for retrieving all genomes with optional pagination and sorting."""
    page: int = Field(1, description="Page number to retrieve.")
    per_page: int = Field(DEFAULT_PER_PAGE_CNT, description="Number of items per page.")
    sortField: Optional[str] = Field(STRAIN_FIELD_ISOLATE_NAME, description="Field to sort by.")
    sortOrder: Optional[str] = Field(DEFAULT_SORT, description="Sort order: 'asc' or 'desc'.")


class GenesByGenomeQuerySchema(BaseModel):
    """Schema for retrieving genes from a specific genome with filters, pagination, and sorting."""
    filter: Optional[str] = Field(
        None,
        description="Additional gene filter, e.g., 'pfam:pf07715;interpro:ipr012910'."
    )
    filter_operators: Optional[str] = Field(
        None,
        description="Logical operators (AND/OR) per facet, e.g., 'pfam:AND;interpro:OR'."
    )
    page: int = Field(1, description="Page number to retrieve.")
    per_page: int = Field(DEFAULT_PER_PAGE_CNT, description="Number of genes to return per page.")
    sort_field: Optional[str] = Field(None, description="Field to sort results by.")
    sort_order: Optional[str] = Field(DEFAULT_SORT, description="Sort order: 'asc' or 'desc'.")


class GenomeDownloadTSVQuerySchema(BaseModel):
    """Schema for downloading genomes as TSV with filtering and sorting."""
    query: str = Field("", description="Search term to match against genome names or metadata.")
    sortField: Optional[str] = Field(STRAIN_FIELD_ISOLATE_NAME, description="Field to sort results by.")
    sortOrder: Optional[str] = Field(DEFAULT_SORT, description="Sort order: 'asc' or 'desc'.")
    isolates: Optional[List[str]] = Field(None, description="List of isolate names to filter.")
    species_acronym: Optional[str] = Field(None, description="Optional species acronym filter.")


class StrainSuggestionSchema(BaseModel):
    isolate_name: str
    assembly_name: str

    model_config = ConfigDict(from_attributes=True)


class StrainMinSchema(BaseModel):
    isolate_name: str
    assembly_name: str

    model_config = ConfigDict(from_attributes=True)


class ContigSchema(BaseModel):
    seq_id: str
    length: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class GenomeResponseSchema(BaseModel):
    species_scientific_name: Optional[str] = None
    species_acronym: Optional[str] = None
    isolate_name: str
    assembly_name: Optional[str]
    assembly_accession: Optional[str]
    fasta_file: str
    gff_file: str
    fasta_url: str
    gff_url: str
    type_strain: bool
    contigs: List[ContigSchema]

    model_config = ConfigDict(from_attributes=True)


class GenomePaginationSchema(BasePaginationSchema):
    results: List[GenomeResponseSchema]


__all__ = [
    "StrainSuggestionSchema",
    "ContigSchema",
    "GenomeResponseSchema",
    "GenomePaginationSchema",
]
