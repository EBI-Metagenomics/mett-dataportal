from typing import List, Dict, Any, Optional, Literal, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator

from dataportal.schema.interactions.ppi_schemas import (
    PPINetworkNodeSchema,
    PPINetworkEdgeSchema,
    PPINetworkPropertiesSchema,
)
from dataportal.schema.response_schemas import SuccessResponseSchema
from dataportal.utils.constants import STRING_NETWORK_TYPE_VALUES


class StringNetworkRowSchema(BaseModel):
    """One raw row from STRING /tsv/network with locus tag mapping."""

    stringId_A: str = Field(..., description="STRING protein ID A (e.g. 820.ERS852554_01920)")
    stringId_B: str = Field(..., description="STRING protein ID B")
    preferredName_A: Optional[str] = None
    preferredName_B: Optional[str] = None
    locus_tag_A: Optional[str] = Field(
        None, description="Locus tag for protein A when mapped from feature/PPI index"
    )
    locus_tag_B: Optional[str] = Field(
        None, description="Locus tag for protein B when mapped from feature/PPI index"
    )
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
    data_sources: List[str] = ["stringdb"]
    edges_filtered_unmapped: Optional[int] = Field(
        None,
        description="Edges removed due to missing locus tag mapping for one or both proteins",
    )
    unmapped_string_ids: Optional[List[str]] = Field(
        None,
        description="STRING IDs with no locus tag mapping (see string_network_service STRING_NETWORK_UNMAPPED_FILTER)",
    )


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

    locus_tag: Optional[str] = Field(
        None,
        description="Gene locus tag. With species_acronym, resolves to STRING ID via feature index and fetches neighborhood (no pair_id needed).",
    )
    pair_id: Optional[str] = Field(
        None,
        description="PPI pair_id for lookup from PPI index (e.g. bu:A0A0X1ABC1__B0ABC123). Use with locus_tag for single-protein neighborhood.",
    )
    protein_ids: Optional[List[str]] = Field(
        None,
        description="Direct STRING protein IDs (e.g. ['820.ERS852554_01920'])",
    )
    species_acronym: Optional[str] = Field(
        None, description="Species acronym (BU, PV) for taxid resolution"
    )
    required_score: Optional[int] = Field(
        None, ge=0, le=1000, description="Minimum STRING score threshold (0-1000)"
    )
    add_nodes: Optional[int] = Field(
        None,
        ge=0,
        description="Number of additional interaction partners to add by confidence (default 10). "
        "Set higher (e.g. 50) to get more interactors.",
    )
    network_type: Literal[STRING_NETWORK_TYPE_VALUES] = Field(
        "physical",
        description="Network type: physical (direct interactions) or functional (physical + indirect associations)",
    )
    evidence_channels: Optional[List[str]] = Field(
        None,
        description="Filter by STRING evidence channels. Include only edges with score>0 in at least one selected channel. "
        "Values: neighborhood, fusion, cooccurrence, coexpression, experimental, database, textmining. "
        "None or empty = no filter (all evidence). Accepts comma-separated string or list.",
    )

    @field_validator("evidence_channels", mode="before")
    @classmethod
    def split_evidence_channels(cls, v: Optional[Union[str, List[str]]]) -> Optional[List[str]]:
        if v is None:
            return None
        if isinstance(v, str):
            parts = [p.strip() for p in v.split(",") if p.strip()]
            return parts if parts else None
        return v if v else None


class StringNetworkDataSchema(BaseModel):
    """Typed payload for STRING network API response (the `data` field)."""

    network: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Raw STRING network edges (TSV rows as dicts with stringId_A/B, preferredName_A/B, scores, etc.)",
    )
    identifiers: List[str] = Field(
        default_factory=list,
        description="STRING protein IDs that were queried",
    )
    species_taxid: Optional[int] = Field(
        None,
        description="NCBI taxonomy ID used for the STRING API call",
    )
    network_url: Optional[str] = Field(
        None,
        description="Link to STRING DB web UI for this network",
    )
    focal_locus_tag: Optional[str] = Field(
        None,
        description="The queried locus tag (when locus_tag was provided); used for merging nodes in 'both' view",
    )
    focal_preferred_name: Optional[str] = Field(
        None,
        description="STRING's preferred name for the focal protein",
    )
    focal_string_id: Optional[str] = Field(
        None,
        description="STRING protein ID of the focal gene",
    )
    data_sources: List[str] = Field(
        default_factory=lambda: ["stringdb"],
        description="Data source identifiers for multi-source graphs",
    )
    error: Optional[str] = Field(
        None,
        description="Error message when STRING fetch failed or gene has no STRING ID",
    )
    interaction: Optional[Dict[str, Any]] = Field(
        None,
        description="PPI interaction record when pair_id was used for lookup",
    )
    edges_filtered_unmapped: Optional[int] = Field(
        None,
        description="Number of edges removed because one or both proteins had no locus tag mapping. "
        "See unmapped_string_ids for excluded STRING IDs.",
    )
    unmapped_string_ids: Optional[List[str]] = Field(
        None,
        description="STRING protein IDs that had no locus tag mapping (feature/PPI index). "
        "Edges involving these proteins were filtered out.",
    )

    model_config = ConfigDict(extra="ignore")


class PPIStringNetworkResponseSchema(SuccessResponseSchema):
    """Response schema for STRING network data."""

    data: StringNetworkDataSchema = Field(
        ...,
        description="STRING network data with locus tag mapping and focal gene info",
    )
