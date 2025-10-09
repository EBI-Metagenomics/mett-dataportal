"""Schemas for operon API endpoints."""

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class OperonSearchQuerySchema(BaseModel):
    """Schema for operon search query parameters."""
    
    locus_tag: Optional[str] = Field(
        None,
        description="Search for operons containing this gene (locus tag)"
    )
    operon_id: Optional[str] = Field(
        None,
        description="Filter by specific operon ID"
    )
    species_acronym: Optional[str] = Field(
        None,
        description="Filter by species acronym"
    )
    isolate_name: Optional[str] = Field(
        None,
        description="Filter by isolate name"
    )
    has_tss: Optional[bool] = Field(
        None,
        description="Filter by presence of transcription start site"
    )
    has_terminator: Optional[bool] = Field(
        None,
        description="Filter by presence of terminator"
    )
    min_gene_count: Optional[int] = Field(
        None,
        ge=2,
        description="Minimum number of genes in operon"
    )
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Results per page")


class OperonGeneQuerySchema(BaseModel):
    """Schema for querying operons by gene."""
    
    locus_tag: str = Field(..., description="Gene locus tag")
    species_acronym: Optional[str] = Field(None, description="Filter by species")


class OperonGeneInfoSchema(BaseModel):
    """Schema for gene information in operon response."""
    
    locus_tag: str
    uniprot_id: Optional[str] = None
    gene_name: Optional[str] = None
    product: Optional[str] = None
    isolate_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class OperonSchema(BaseModel):
    """Schema for operon response."""
    
    operon_id: str
    isolate_name: Optional[str] = None
    species_acronym: Optional[str] = None
    species_scientific_name: Optional[str] = None
    genes: List[str] = Field(default_factory=list, description="List of gene locus tags in operon")
    gene_count: int = 0
    has_tss: bool = False
    has_terminator: bool = False
    gene_a: Optional[OperonGeneInfoSchema] = None
    gene_b: Optional[OperonGeneInfoSchema] = None
    
    model_config = ConfigDict(from_attributes=True)


class OperonDetailSchema(BaseModel):
    """Detailed schema for operon with all gene information."""
    
    operon_id: str
    isolate_name: Optional[str] = None
    species_acronym: Optional[str] = None
    species_scientific_name: Optional[str] = None
    gene_count: int = 0
    has_tss: bool = False
    has_terminator: bool = False
    genes: List[OperonGeneInfoSchema] = Field(
        default_factory=list,
        description="Detailed information for all genes in operon"
    )
    
    model_config = ConfigDict(from_attributes=True)

