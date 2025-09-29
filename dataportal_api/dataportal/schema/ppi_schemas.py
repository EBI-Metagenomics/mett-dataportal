from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from dataportal.schema.response_schemas import PaginatedResponseSchema, SuccessResponseSchema
from dataportal.schema.base_schemas import BasePaginationSchema


class PPIInteractionSchema(BaseModel):
    """Schema for a single PPI interaction."""
    pair_id: str
    species_scientific_name: Optional[str] = None
    species_acronym: Optional[str] = None
    isolate_name: Optional[str] = None
    protein_a: str
    protein_b: str
    participants: List[str]
    is_self_interaction: bool = False
    
    # Gene information for protein_a
    protein_a_locus_tag: Optional[str] = None
    protein_a_uniprot_id: Optional[str] = None
    protein_a_name: Optional[str] = None
    protein_a_product: Optional[str] = None
    
    # Gene information for protein_b
    protein_b_locus_tag: Optional[str] = None
    protein_b_uniprot_id: Optional[str] = None
    protein_b_name: Optional[str] = None
    protein_b_product: Optional[str] = None
    
    # Scores
    dl_score: Optional[float] = None
    comelt_score: Optional[float] = None
    perturbation_score: Optional[float] = None
    abundance_score: Optional[float] = None
    melt_score: Optional[float] = None
    secondary_score: Optional[float] = None
    bayesian_score: Optional[float] = None
    string_score: Optional[float] = None
    operon_score: Optional[float] = None
    ecocyc_score: Optional[float] = None
    tt_score: Optional[float] = None
    ds_score: Optional[float] = None
    
    # Evidence flags
    has_xlms: bool = False
    has_string: bool = False
    has_operon: bool = False
    has_ecocyc: bool = False
    has_experimental: bool = False
    
    # Metadata
    evidence_count: int = 0
    confidence_bin: Optional[str] = None


class PPISearchQuerySchema(BaseModel):
    """Schema for PPI search queries."""
    species_acronym: Optional[str] = Field(None, description="Species acronym (e.g., 'PV', 'BU')")
    isolate_name: Optional[str] = Field(None, description="Isolate name (e.g., 'BU_ATCC8492', 'PV_ATCC8482')")
    score_type: Optional[str] = Field(None, description="Score type to filter by")
    score_threshold: Optional[float] = Field(None, description="Minimum score threshold")
    has_xlms: Optional[bool] = Field(None, description="Filter by XL-MS evidence")
    has_string: Optional[bool] = Field(None, description="Filter by STRING evidence")
    has_operon: Optional[bool] = Field(None, description="Filter by operon evidence")
    has_ecocyc: Optional[bool] = Field(None, description="Filter by EcoCyc evidence")
    has_experimental: Optional[bool] = Field(None, description="Filter by experimental evidence")
    confidence_bin: Optional[str] = Field(None, description="Filter by confidence level (high, medium, low)")
    protein_id: Optional[str] = Field(None, description="Filter interactions involving specific protein")
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100000, description="Results per page")


class PPINetworkSchema(BaseModel):
    """Schema for PPI network data."""
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    properties: Dict[str, Any]


class PPINetworkPropertiesSchema(BaseModel):
    """Schema for network properties."""
    num_nodes: int
    num_edges: int
    density: float
    avg_clustering_coefficient: float
    degree_distribution: List[int]


class PPINeighborhoodSchema(BaseModel):
    """Schema for protein neighborhood data."""
    protein_id: str
    neighbors: List[Dict[str, Any]]
    network_data: PPINetworkSchema


class PPIPaginationSchema(BasePaginationSchema):
    """Pagination schema for PPI interactions."""
    results: List[PPIInteractionSchema]

class PPISearchResponseSchema(PaginatedResponseSchema):
    """Response schema for PPI search results."""
    data: List[PPIInteractionSchema]


class PPINetworkResponseSchema(SuccessResponseSchema):
    """Response schema for PPI network data."""
    data: PPINetworkSchema


class PPINetworkPropertiesResponseSchema(SuccessResponseSchema):
    """Response schema for network properties."""
    data: PPINetworkPropertiesSchema


class PPINeighborhoodResponseSchema(SuccessResponseSchema):
    """Response schema for protein neighborhood data."""
    data: PPINeighborhoodSchema
