from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from dataportal.schema.core.genome_schemas import StrainAnnotationSchema


class GenomeReleaseAppearanceSchema(BaseModel):
    version: str
    status: str
    is_current: bool
    annotation: Optional[StrainAnnotationSchema] = None

    model_config = ConfigDict(from_attributes=True)


class GenomeReleaseHistorySchema(BaseModel):
    isolate_name: str
    appearances: List[GenomeReleaseAppearanceSchema] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class GeneReleaseAppearanceSchema(BaseModel):
    version: str
    status: str
    is_current: bool
    annotation: Optional[StrainAnnotationSchema] = None
    isolate_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class GeneReleaseHistorySchema(BaseModel):
    locus_tag: str
    appearances: List[GeneReleaseAppearanceSchema] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
