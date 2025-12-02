"""Schemas for ortholog API endpoints."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from dataportal.schema.base_schemas import BasePaginationSchema


class OrthologSearchQuerySchema(BaseModel):
    """Schema for ortholog search query parameters."""

    locus_tag: Optional[str] = Field(
        None, description="Search for orthologs of this gene (locus tag)"
    )
    species_acronym: Optional[str] = Field(None, description="Filter by species acronym")
    orthology_type: Optional[str] = Field(
        None, description="Filter by orthology type (1:1, many:1, 1:many, many:many)"
    )
    one_to_one_only: bool = Field(False, description="Return only one-to-one orthologs")
    cross_species_only: bool = Field(
        False, description="Return only cross-species orthologs (exclude same species)"
    )
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Results per page")


class OrthologPairQuerySchema(BaseModel):
    """Schema for querying ortholog relationship between two genes."""

    locus_tag_a: str = Field(..., description="First gene locus tag")
    locus_tag_b: str = Field(..., description="Second gene locus tag")


class OrthologGeneInfoSchema(BaseModel):
    """Schema for gene information in ortholog response."""

    locus_tag: str
    uniprot_id: Optional[str] = None
    gene_name: Optional[str] = None
    product: Optional[str] = None
    start: Optional[int] = None
    end: Optional[int] = None
    strand: Optional[str] = None
    species_acronym: Optional[str] = None
    isolate: Optional[str] = None

    # Relationship metadata (varies per pair)
    orthology_type: Optional[str] = Field(
        None, description="Type of orthology relationship (1:1, many:1, etc.)"
    )
    oma_group_id: Optional[int] = Field(None, description="OMA group identifier")
    is_one_to_one: bool = Field(False, description="True if one-to-one orthology")

    model_config = ConfigDict(from_attributes=True)


class OrthologPairSchema(BaseModel):
    """Schema for ortholog pair response."""

    pair_id: str
    orthology_type: Optional[str] = None
    oma_group_id: Optional[int] = None
    is_one_to_one: bool = False
    same_species: bool = False
    same_isolate: bool = False
    gene_a: OrthologGeneInfoSchema
    gene_b: OrthologGeneInfoSchema

    model_config = ConfigDict(from_attributes=True)


class OrthologsByGeneSchema(BaseModel):
    """Schema for orthologs of a specific gene."""

    query_gene: str
    orthologs: List[OrthologGeneInfoSchema]
    total_count: int
    one_to_one_count: int
    cross_species_count: int

    model_config = ConfigDict(from_attributes=True)


class OrthologSearchPaginationSchema(BasePaginationSchema):
    """Pagination schema for ortholog search results."""

    results: List[Dict[str, Any]]
