from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field

from dataportal.schema.base_schemas import BasePaginationSchema


class ProteomicsDataSchema(BaseModel):
    """Schema for individual proteomics evidence entry."""
    
    coverage: Optional[float] = Field(None, description="Protein sequence coverage percentage")
    unique_peptides: Optional[int] = Field(None, description="Number of unique peptides identified")
    unique_intensity: Optional[float] = Field(None, description="Unique peptide intensity measurement")
    evidence: Optional[bool] = Field(None, description="Whether proteomics evidence exists (Y/N)")
    
    model_config = ConfigDict(from_attributes=True)


class BasicGeneInfoSchema(BaseModel):
    """Basic gene information for proteomics responses."""
    
    locus_tag: Optional[str] = None
    gene_name: Optional[str] = None
    uniprot_id: Optional[str] = None
    product: Optional[str] = None
    isolate_name: Optional[str] = None
    species_scientific_name: Optional[str] = None
    species_acronym: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class ProteomicsWithGeneSchema(BaseModel):
    """Schema combining proteomics evidence with basic gene/feature information."""
    
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
    
    # Proteomics evidence data (array of entries)
    proteomics: Optional[List[ProteomicsDataSchema]] = Field(
        default_factory=list,
        description="Array of proteomics evidence entries for this gene"
    )
    
    model_config = ConfigDict(from_attributes=True)


class ProteomicsSearchQuerySchema(BaseModel):
    """Schema for proteomics search endpoint query parameters."""
    
    locus_tags: Optional[str] = Field(
        None,
        description="Comma-separated list of locus tags to search for",
        examples=["BU_ATCC8492_00002,BU_ATCC8492_00002"]
    )
    uniprot_ids: Optional[str] = Field(
        None,
        description="Comma-separated list of UniProt IDs to search for",
        examples=["A7V2E9,A7V2F0"]
    )
    min_coverage: Optional[float] = Field(
        None,
        description="Minimum coverage percentage filter",
        ge=0,
        le=100
    )
    min_unique_peptides: Optional[int] = Field(
        None,
        description="Minimum number of unique peptides filter",
        ge=0
    )
    has_evidence: Optional[bool] = Field(
        None,
        description="Filter by proteomics evidence flag (true/false)"
    )
    
    model_config = ConfigDict(from_attributes=True)


class ProteomicsPaginationSchema(BasePaginationSchema):
    """Paginated response schema for proteomics data."""
    
    results: List[ProteomicsWithGeneSchema]


__all__ = [
    "ProteomicsDataSchema",
    "BasicGeneInfoSchema",
    "ProteomicsWithGeneSchema",
    "ProteomicsSearchQuerySchema",
    "ProteomicsPaginationSchema",
]

