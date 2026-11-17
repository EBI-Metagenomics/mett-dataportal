from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from dataportal.schema.response_schemas import PaginatedResponseSchema, SuccessResponseSchema
from dataportal.schema.base_schemas import BasePaginationSchema
from dataportal.utils.constants import PPI_SCORE_FIELDS, PPI_VALID_FILTER_FIELDS


class PPIInteractionSchema(BaseModel):
    """Schema for a single PPI interaction."""

    pair_id: str
    species_scientific_name: Optional[str] = None
    species_acronym: Optional[str] = None
    isolate_name: Optional[str] = None
    protein_a: str
    protein_b: str
    participants: List[str]
    participants_locus_tag: Optional[List[str]] = None
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

    # External identifiers (STRING DB)
    string_protein_a_id: Optional[str] = None
    string_protein_b_id: Optional[str] = None

    # PPI v4 consensus and evidence-category scores
    consensus_score: Optional[float] = None
    raw_consensus_score: Optional[float] = None
    consensus_rank: Optional[int] = None
    edge_id: Optional[str] = None
    q_ppi: Optional[float] = None
    q_chemical_genetic: Optional[float] = None
    q_coexpression: Optional[float] = None
    q_operons: Optional[float] = None
    q_metabolic: Optional[float] = None

    # Supporting network counts
    n_evidence_types: Optional[int] = None
    n_networks_total: Optional[int] = None
    n_ppi: Optional[int] = None
    n_chemical_genetic: Optional[int] = None
    n_coexpression: Optional[int] = None
    n_operons: Optional[int] = None
    n_metabolic: Optional[int] = None

    # Evidence-category presence
    has_ppi: bool = False
    has_chemical_genetic: bool = False
    has_coexpression: bool = False
    has_operons: bool = False
    has_metabolic: bool = False

    # Metadata
    evidence_count: int = 0


class PPISearchQuerySchema(BaseModel):
    """Schema for PPI search queries."""

    species_acronym: Optional[str] = Field(None, description="Species acronym (e.g., 'PV', 'BU')")
    isolate_name: Optional[str] = Field(
        None, description="Isolate name (e.g., 'BU_ATCC8492', 'PV_ATCC8482')"
    )
    score_type: Optional[str] = Field(
        None,
        description=(
            "Score used to filter interactions. One of consensus_score, raw_consensus_score, "
            "q_ppi, q_chemical_genetic, q_coexpression, q_operons, q_metabolic "
            "(short aliases such as ppi or operons are accepted)."
        ),
    )
    score_threshold: Optional[float] = Field(None, description="Minimum score threshold")
    has_ppi: Optional[bool] = Field(None, description="Filter by PPI-category evidence")
    has_chemical_genetic: Optional[bool] = Field(
        None, description="Filter by chemical-genetic evidence"
    )
    has_coexpression: Optional[bool] = Field(None, description="Filter by co-expression evidence")
    has_operons: Optional[bool] = Field(None, description="Filter by operon evidence")
    has_metabolic: Optional[bool] = Field(None, description="Filter by metabolic evidence")
    protein_id: Optional[str] = Field(
        None, description="Filter interactions involving specific protein"
    )
    locus_tag: Optional[str] = Field(
        None, description="Filter interactions involving specific locus tag"
    )
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100000, description="Results per page")

    @validator("score_type")
    def validate_score_type(cls, v):
        if v is not None and v not in PPI_VALID_FILTER_FIELDS:
            raise ValueError(f"Invalid score_type: {v}. Valid options: {PPI_SCORE_FIELDS}")
        return v

    @validator("locus_tag")
    def validate_protein_identifier(cls, v, values):
        """Validate that only one of protein_id or locus_tag is provided."""
        protein_id = values.get("protein_id")
        if v is not None and protein_id is not None:
            raise ValueError("Only one of 'protein_id' or 'locus_tag' can be provided, not both")
        return v


class PPINetworkNodeSchema(BaseModel):
    """Schema for a PPI network node."""

    id: str = Field(..., description="Protein ID (UniProt ID)")
    locus_tag: Optional[str] = Field(None, description="Locus tag of the gene")
    name: Optional[str] = Field(None, description="Gene name")
    product: Optional[str] = Field(None, description="Gene product description")


class PPINetworkEdgeSchema(BaseModel):
    """Schema for a PPI network edge."""

    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    weight: Optional[float] = Field(
        None, description="Edge weight from the selected score (default: consensus_score)"
    )
    pair_id: Optional[str] = Field(None, description="Canonical interaction pair ID")
    consensus_score: Optional[float] = Field(None, description="PPI v4 consensus score")
    raw_consensus_score: Optional[float] = Field(None, description="Unnormalized consensus score")
    n_evidence_types: Optional[int] = Field(
        None, description="Number of evidence categories supporting this interaction"
    )
    n_networks_total: Optional[int] = Field(
        None, description="Total supporting networks across all evidence categories"
    )
    evidence_scores: Optional[Dict[str, float]] = Field(
        None, description="Non-zero evidence-category scores (Q_PPI, Q_Operons, and so on)"
    )
    network_counts: Optional[Dict[str, int]] = Field(
        None, description="Non-zero per-category network counts"
    )


class PPINetworkSchema(BaseModel):
    """Schema for PPI network data."""

    nodes: List[PPINetworkNodeSchema]
    edges: List[PPINetworkEdgeSchema]
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


class PPIAllNeighborsSchema(BaseModel):
    """Schema for all protein neighbors (raw data without algorithm processing)."""

    protein_id: str
    total_interactions: int
    interactions: List[PPIInteractionSchema]
    unique_neighbors: List[Dict[str, Any]]  # List of unique neighbor proteins with metadata


class PPIAllNeighborsResponseSchema(SuccessResponseSchema):
    """Response schema for all protein neighbors data."""

    data: PPIAllNeighborsSchema


# Request Schemas
class PPINeighborhoodQuerySchema(BaseModel):
    """Schema for protein neighborhood query parameters."""

    protein_id: Optional[str] = Field(None, description="UniProt ID of the protein")
    locus_tag: Optional[str] = Field(None, description="Locus tag of the protein")
    string_id: Optional[str] = Field(
        None,
        description="STRING DB protein ID (e.g. 820.ERS852554_03539). Resolved to locus_tag via feature index; if no mapping, returns empty neighborhood.",
    )
    n: int = Field(5, ge=1, le=50, description="Number of neighbors to retrieve")
    species_acronym: Optional[str] = Field(None, description="Species acronym filter")
    score_type: Optional[str] = Field(
        "consensus_score",
        description="Score type used to rank and filter interactions (default: consensus_score). Determines which interactions are considered and their order for 'top N'.",
    )
    score_threshold: Optional[float] = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Minimum score threshold; only interactions with score >= this value are considered when building the neighborhood.",
    )

    @validator("locus_tag")
    def validate_protein_identifier(cls, v, values):
        """Validate that only one of protein_id, locus_tag, or string_id is provided."""
        protein_id = values.get("protein_id")
        string_id = values.get("string_id")
        if v is not None and (protein_id is not None or string_id is not None):
            raise ValueError(
                "Only one of 'protein_id', 'locus_tag', or 'string_id' can be provided, not multiple"
            )
        return v


class PPINeighborsQuerySchema(BaseModel):
    """Schema for protein neighbors query parameters."""

    protein_id: Optional[str] = Field(None, description="UniProt ID of the protein")
    locus_tag: Optional[str] = Field(None, description="Locus tag of the protein")
    species_acronym: Optional[str] = Field(None, description="Species acronym filter")

    @validator("locus_tag")
    def validate_protein_identifier(cls, v, values):
        """Validate that only one of protein_id or locus_tag is provided."""
        protein_id = values.get("protein_id")
        if v is not None and protein_id is not None:
            raise ValueError("Only one of 'protein_id' or 'locus_tag' can be provided, not both")
        return v


class PPINetworkQuerySchema(BaseModel):
    """Schema for PPI network query parameters."""

    score_threshold: float = Field(
        0.8, ge=0.0, le=1.0, description="Score threshold for network construction"
    )
    species_acronym: Optional[str] = Field(None, description="Species acronym filter")
    isolate_name: Optional[str] = Field(
        None, description="Isolate name filter (e.g., 'BU_ATCC8492', 'PV_ATCC8482')"
    )
    locus_tag: Optional[str] = Field(
        None, description="Filter to PPIs involving this locus_tag (creates neighborhood view)"
    )
    include_properties: bool = Field(False, description="Whether to include network properties")


class PPINetworkPropertiesQuerySchema(BaseModel):
    """Schema for PPI network properties query parameters."""

    score_type: str = Field(..., description="Score type for network construction")
    score_threshold: float = Field(
        0.8, ge=0.0, le=1.0, description="Score threshold for network construction"
    )
    species_acronym: Optional[str] = Field(None, description="Species acronym filter")
    isolate_name: Optional[str] = Field(
        None, description="Isolate name filter (e.g., 'BU_ATCC8492', 'PV_ATCC8482')"
    )


class PPIScoreTypesResponseSchema(SuccessResponseSchema):
    """Response schema for available score types."""

    data: Dict[str, Any] = Field(
        ...,
        description=(
            "Available score types and evidence channel metadata. "
            "Example: {'score_types': [...], 'default': 'consensus_score', "
            "'evidence_channels': {'q_ppi': 'PPI', 'q_operons': 'Operons', ...}}."
        ),
    )


class PPIInteractionDetailResponseSchema(SuccessResponseSchema):
    """Response schema for a single PPI interaction by pair_id."""

    data: PPIInteractionSchema


class PPIDataSourcesResponseSchema(SuccessResponseSchema):
    """Response schema for available PPI data sources (local ES, STRING DB, etc.)."""

    data: Dict[str, Any] = Field(
        ...,
        description=(
            "Available PPI data sources and defaults. "
            "Example: {'sources': ['local_es', 'stringdb'], 'default': 'local_es'}."
        ),
    )
