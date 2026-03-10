from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from dataportal.schema.interactions.ppi_schemas import (
    PPINetworkNodeSchema,
    PPINetworkEdgeSchema,
    PPINetworkPropertiesSchema,
)
from dataportal.schema.response_schemas import SuccessResponseSchema


class StringNetworkRowSchema(BaseModel):
    """One raw row from STRING /tsv/network."""

    stringId_A: str = Field(..., description="STRING protein ID A (e.g. 820.ERS852554_01920)")
    stringId_B: str = Field(..., description="STRING protein ID B")
    preferredName_A: Optional[str] = None
    preferredName_B: Optional[str] = None
    ncbiTaxonId: Optional[int] = None

    # STRING score fields
    score: Optional[float] = None
    nscore: Optional[float] = None
    fscore: Optional[float] = None
    pscore: Optional[float] = None
    ascore: Optional[float] = None
    escore: Optional[float] = None
    dscore: Optional[float] = None
    tscore: Optional[float] = None


class StringNetworkMetadataSchema(BaseModel):
    network_url: Optional[str] = None
    raw_text: Optional[str] = None
    identifiers: List[str] = []
    species_taxid: Optional[int] = None
    focal_preferred_name: Optional[str] = None
    preferred_name_to_locus_tag: Dict[str, str] = {}
    data_sources: List[str] = ["stringdb"]


class StringNetworkNormalizedSchema(BaseModel):
    """STRING network normalized to our generic PPI network shape."""

    nodes: List[PPINetworkNodeSchema]
    edges: List[PPINetworkEdgeSchema]
    properties: PPINetworkPropertiesSchema


class StringNetworkResponseSchema(BaseModel):
    """Payload for /ppi/string-network."""

    rows: List[StringNetworkRowSchema]
    metadata: StringNetworkMetadataSchema
    normalized_network: StringNetworkNormalizedSchema


# STRING DB network schemas
class PPIStringNetworkQuerySchema(BaseModel):
    """Schema for STRING network query parameters."""

    pair_id: Optional[str] = Field(
        None, description="PPI pair_id to look up (e.g. bu:A0A0X1ABC1__B0ABC123)"
    )
    protein_ids: Optional[List[str]] = Field(
        None,
        description="STRING protein IDs (e.g. ['820.ERS852554_01920', '820.ERS852554_01919'])",
    )
    locus_tag: Optional[str] = Field(
        None,
        description="When using pair_id: use only the STRING ID for this protein (neighborhood of one gene). Omit to get subnetwork for both proteins in the pair.",
    )
    species_acronym: Optional[str] = Field(
        None, description="Species acronym (BU, PV) for taxid resolution"
    )
    required_score: Optional[int] = Field(
        None, ge=0, le=1000, description="Minimum STRING score threshold (0-1000)"
    )
    network_type: str = Field("physical", description="Network type: physical or functional")


class PPIStringNetworkResponseSchema(SuccessResponseSchema):
    """Response schema for STRING network data."""

    data: Dict[str, Any] = Field(..., description="STRING network data and interaction metadata")
