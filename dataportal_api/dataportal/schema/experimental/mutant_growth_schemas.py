from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field

from dataportal.schema.base_schemas import BasePaginationSchema


class MutantGrowthDataSchema(BaseModel):
    """Schema for individual mutant growth data entry."""
    
    doubling_time: Optional[float] = Field(None, description="Doubling time in hours")
    isdoublepicked: Optional[bool] = Field(None, description="Whether mutant was picked twice (not truly independent replicates)")
    brep: Optional[str] = Field(None, description="Biological replicate identifier (brep_1, brep_2, etc.)")
    plate384: Optional[int] = Field(None, description="Position in 384-well arrayed library")
    well384: Optional[str] = Field(None, description="Well position (A17, C16, etc.)")
    percent_from_start: Optional[float] = Field(None, description="Transposon insertion position in gene (0-1)")
    media: Optional[str] = Field(None, description="Experimental media/condition (e.g., 'caecal')")
    experimental_condition: Optional[str] = Field(None, description="Overall experimental context")
    
    model_config = ConfigDict(from_attributes=True)


class MutantGrowthWithGeneSchema(BaseModel):
    """Schema combining mutant growth data with basic gene/feature information."""
    
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
    
    # Mutant growth data (array of entries)
    mutant_growth: Optional[List[MutantGrowthDataSchema]] = Field(
        default_factory=list,
        description="Array of mutant growth data entries for this gene"
    )
    
    model_config = ConfigDict(from_attributes=True)


class MutantGrowthSearchQuerySchema(BaseModel):
    """Schema for mutant growth search endpoint query parameters."""
    
    locus_tags: Optional[str] = Field(
        None,
        description="Comma-separated list of locus tags to search for"
    )
    uniprot_ids: Optional[str] = Field(
        None,
        description="Comma-separated list of UniProt IDs to search for"
    )
    media: Optional[str] = Field(
        None,
        description="Filter by growth media"
    )
    experimental_condition: Optional[str] = Field(
        None,
        description="Filter by experimental condition"
    )
    min_doubling_time: Optional[float] = Field(
        None,
        description="Minimum doubling time in hours",
        ge=0
    )
    max_doubling_time: Optional[float] = Field(
        None,
        description="Maximum doubling time in hours",
        ge=0
    )
    exclude_double_picked: Optional[bool] = Field(
        None,
        description="Exclude double-picked mutants (isdoublepicked=True)"
    )
    
    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "MutantGrowthDataSchema",
    "MutantGrowthWithGeneSchema",
    "MutantGrowthSearchQuerySchema",
]

