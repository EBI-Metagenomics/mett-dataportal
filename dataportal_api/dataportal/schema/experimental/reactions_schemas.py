from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field

from dataportal.schema.base_schemas import BasePaginationSchema


class ReactionDetailSchema(BaseModel):
    """Schema for individual reaction detail entry."""
    
    reaction: Optional[str] = Field(None, description="Reaction identifier")
    gpr: Optional[str] = Field(None, description="Gene-protein-reaction rule")
    substrates: Optional[List[str]] = Field(default_factory=list, description="Substrate metabolites")
    products: Optional[List[str]] = Field(default_factory=list, description="Product metabolites")
    metabolites: Optional[List[str]] = Field(default_factory=list, description="All involved metabolites")
    
    model_config = ConfigDict(from_attributes=True)


class ReactionsWithGeneSchema(BaseModel):
    """Schema combining reaction data with basic gene/feature information."""
    
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
    
    # Reaction data
    reactions: Optional[List[str]] = Field(
        default_factory=list,
        description="List of reaction identifiers"
    )
    reaction_details: Optional[List[ReactionDetailSchema]] = Field(
        default_factory=list,
        description="Detailed reaction information including GPR and metabolites"
    )
    
    model_config = ConfigDict(from_attributes=True)


class ReactionsSearchQuerySchema(BaseModel):
    """Schema for reactions search endpoint query parameters."""
    
    locus_tags: Optional[str] = Field(
        None,
        description="Comma-separated list of locus tags to search for"
    )
    uniprot_ids: Optional[str] = Field(
        None,
        description="Comma-separated list of UniProt IDs to search for"
    )
    reaction_id: Optional[str] = Field(
        None,
        description="Filter by reaction identifier"
    )
    metabolite: Optional[str] = Field(
        None,
        description="Filter by metabolite involvement (substrate or product)"
    )
    substrate: Optional[str] = Field(
        None,
        description="Filter by substrate metabolite"
    )
    product: Optional[str] = Field(
        None,
        description="Filter by product metabolite"
    )
    
    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "ReactionDetailSchema",
    "ReactionsWithGeneSchema",
    "ReactionsSearchQuerySchema",
]

