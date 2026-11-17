"""Request and response models for multi-gene PPI path search."""

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from dataportal.schema.interactions.ppi_schemas import PPINetworkEdgeSchema
from dataportal.schema.response_schemas import SuccessResponseSchema


class PPIPathsQuerySchema(BaseModel):
    """Genes of interest and the same score filter the neighborhood view uses."""

    locus_tags: List[str] = Field(..., description="2 to 5 locus tags")
    species_acronym: Optional[str] = Field(None, description="Species acronym, e.g. BU")
    score_type: str = Field("consensus_score", description="Score field used to rank edges")
    score_threshold: float = Field(0.0, ge=0.0, le=1.0, description="Minimum score")

    @field_validator("locus_tags")
    @classmethod
    def clean_locus_tags(cls, value: List[str]) -> List[str]:
        cleaned: List[str] = []
        seen: set[str] = set()
        for raw in value:
            tag = (raw or "").strip()
            if not tag:
                raise ValueError("locus_tags cannot contain blank values")
            if tag in seen:
                raise ValueError(f"Duplicate locus tag: {tag}")
            seen.add(tag)
            cleaned.append(tag)
        if len(cleaned) < 2 or len(cleaned) > 5:
            raise ValueError("Provide between 2 and 5 locus tags")
        return cleaned


class PPIPathNodeSchema(BaseModel):
    id: str
    locus_tag: Optional[str] = None
    name: Optional[str] = None
    product: Optional[str] = None
    role: str = Field(..., description="seed or intermediate")


class PPIPathSchema(BaseModel):
    locus_tags: List[str]
    protein_ids: List[str]


class PPIDisconnectedPairSchema(BaseModel):
    locus_tag_a: str
    locus_tag_b: str


class PPIPathsDataSchema(BaseModel):
    seeds: List[PPIPathNodeSchema]
    intermediates: List[PPIPathNodeSchema]
    edges: List[PPINetworkEdgeSchema]
    paths: List[PPIPathSchema]
    disconnected_pairs: List[PPIDisconnectedPairSchema]


class PPIPathsResponseSchema(SuccessResponseSchema):
    data: PPIPathsDataSchema
