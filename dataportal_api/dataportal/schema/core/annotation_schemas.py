from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AnnotationRunSchema(BaseModel):
    id: int
    isolate_name: str
    strain_id: Optional[str] = None
    release_label: str
    is_current: bool
    status: str
    mettannotator_version: Optional[str] = None
    pipeline_version: Optional[str] = None
    doc_link: Optional[str] = None
    comments: Optional[str] = None
    processed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    es_feature_index: Optional[str] = None
    gff_file: Optional[str] = None
    gff_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class GenomeAnnotationsResponseSchema(BaseModel):
    isolate_name: str
    current: Optional[AnnotationRunSchema] = None
    previous: List[AnnotationRunSchema] = Field(default_factory=list)
    runs: List[AnnotationRunSchema] = Field(default_factory=list)
