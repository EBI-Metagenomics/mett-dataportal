from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field

from dataportal.schema.base_schemas import BasePaginationSchema


class EssentialityDataSchema(BaseModel):
    """Schema for individual essentiality data entry."""
    
    TAs_in_locus: Optional[int] = Field(None, description="Number of transposon insertion sites in locus")
    TAs_hit: Optional[float] = Field(None, description="Fraction of transposon sites hit (0-1)")
    essentiality_call: Optional[str] = Field(None, description="Essentiality call (essential, not_essential, essential_solid, essential_liquid, unclear)")
    experimental_condition: Optional[str] = Field(None, description="Experimental condition/media")
    element: Optional[str] = Field(None, description="Element type (gene, intergenic, etc.)")
    
    model_config = ConfigDict(from_attributes=True)


class BasicGeneInfoSchema(BaseModel):
    """Basic gene information for essentiality responses."""
    
    locus_tag: Optional[str] = None
    gene_name: Optional[str] = None
    uniprot_id: Optional[str] = None
    product: Optional[str] = None
    isolate_name: Optional[str] = None
    species_scientific_name: Optional[str] = None
    species_acronym: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class EssentialityWithGeneSchema(BaseModel):
    """Schema combining essentiality data with basic gene information."""
    
    # Basic gene info
    locus_tag: Optional[str] = None
    gene_name: Optional[str] = None
    uniprot_id: Optional[str] = None
    product: Optional[str] = None
    isolate_name: Optional[str] = None
    species_scientific_name: Optional[str] = None
    species_acronym: Optional[str] = None
    
    # Essentiality data (array of entries)
    essentiality_data: Optional[List[EssentialityDataSchema]] = Field(
        default_factory=list,
        description="Array of essentiality data entries for this gene"
    )
    
    model_config = ConfigDict(from_attributes=True)


class EssentialitySearchQuerySchema(BaseModel):
    """Schema for essentiality search endpoint query parameters."""
    
    locus_tags: Optional[str] = Field(
        None,
        description="Comma-separated list of locus tags to search for",
        examples=["BU_ATCC8492_00002,BU_ATCC8492_00003"]
    )
    uniprot_ids: Optional[str] = Field(
        None,
        description="Comma-separated list of UniProt IDs to search for",
        examples=["A7V2E9,A7V2F0"]
    )
    essentiality_call: Optional[str] = Field(
        None,
        description="Filter by essentiality call (essential, not_essential, essential_solid, essential_liquid, unclear)"
    )
    experimental_condition: Optional[str] = Field(
        None,
        description="Filter by experimental condition/media"
    )
    min_TAs_in_locus: Optional[int] = Field(
        None,
        description="Minimum number of transposon insertion sites",
        ge=0
    )
    min_TAs_hit: Optional[float] = Field(
        None,
        description="Minimum fraction of transposon sites hit (0-1)",
        ge=0,
        le=1
    )
    element: Optional[str] = Field(
        None,
        description="Filter by element type (gene, intergenic, etc.)"
    )
    
    model_config = ConfigDict(from_attributes=True)


class EssentialityPaginationSchema(BasePaginationSchema):
    """Paginated response schema for essentiality data."""
    
    results: List[EssentialityWithGeneSchema]


__all__ = [
    "EssentialityDataSchema",
    "BasicGeneInfoSchema",
    "EssentialityWithGeneSchema",
    "EssentialitySearchQuerySchema",
    "EssentialityPaginationSchema",
]

