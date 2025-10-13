from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field

from dataportal.schema.base_schemas import BasePaginationSchema


class FitnessDataSchema(BaseModel):
    """Schema for individual fitness data entry."""
    
    experimental_condition: Optional[str] = Field(None, description="Experimental condition")
    # media: Optional[str] = Field(None, description="Growth media")
    contrast: Optional[str] = Field(None, description="Contrast/comparison")
    lfc: Optional[float] = Field(None, description="Log fold change")
    fdr: Optional[float] = Field(None, description="False discovery rate")
    number_of_barcodes: Optional[int] = Field(None, description="Number of barcodes (reliability indicator)")
    
    model_config = ConfigDict(from_attributes=True)


class FitnessWithGeneSchema(BaseModel):
    """Schema combining fitness data with basic gene/feature information."""
    
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
    
    # Fitness data (array of entries)
    fitness: Optional[List[FitnessDataSchema]] = Field(
        default_factory=list,
        description="Array of fitness data entries for this gene"
    )
    
    model_config = ConfigDict(from_attributes=True)


class FitnessSearchQuerySchema(BaseModel):
    """Schema for fitness search endpoint query parameters."""
    
    locus_tags: Optional[str] = Field(
        None,
        description="Comma-separated list of locus tags to search for"
    )
    uniprot_ids: Optional[str] = Field(
        None,
        description="Comma-separated list of UniProt IDs to search for"
    )
    # media: Optional[str] = Field(
    #     None,
    #     description="Filter by growth media"
    # )
    contrast: Optional[str] = Field(
        None,
        description="Filter by contrast"
    )
    min_lfc: Optional[float] = Field(
        None,
        description="Minimum log fold change (absolute value)"
    )
    max_fdr: Optional[float] = Field(
        None,
        description="Maximum false discovery rate",
        ge=0,
        le=1
    )
    min_barcodes: Optional[int] = Field(
        None,
        description="Minimum number of barcodes",
        ge=0
    )
    
    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "FitnessDataSchema",
    "FitnessWithGeneSchema",
    "FitnessSearchQuerySchema",
]

