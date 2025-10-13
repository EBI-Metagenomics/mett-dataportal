from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field

from dataportal.schema.base_schemas import BasePaginationSchema


class EssentialityDataSchema(BaseModel):
    """Schema for individual essentiality data entry."""
    
    tas_in_locus: Optional[int] = Field(
        None, 
        alias="TAs_in_locus",
        description="Number of transposon insertion sites in locus"
    )
    tas_hit: Optional[float] = Field(
        None, 
        alias="TAs_hit",
        description="Fraction of transposon sites hit (0-1)"
    )
    essentiality_call: Optional[str] = Field(None, description="Essentiality call (essential, not_essential, essential_solid, essential_liquid, unclear)")
    experimental_condition: Optional[str] = Field(None, description="Experimental condition/media")
    element: Optional[str] = Field(None, description="Element type (gene, intergenic, etc.)")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


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
    """Schema combining essentiality data with basic gene/feature information."""
    
    # Feature identification (required for both genes and intergenic)
    feature_id: Optional[str] = Field(None, description="Unique feature identifier (ES document ID)")
    feature_type: Optional[str] = Field(None, description="Feature type (gene or IG)")
    
    # Basic gene info (may be null for intergenic features)
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
    min_tas_in_locus: Optional[int] = Field(
        None,
        description="Minimum number of transposon insertion sites",
        ge=0
    )
    min_tas_hit: Optional[float] = Field(
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

