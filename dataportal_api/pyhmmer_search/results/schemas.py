import json
from typing import Literal, Optional, List

from django_celery_results.models import TaskResult
from ninja import ModelSchema
from ninja import Schema, Field
from pydantic import UUID4, field_validator
from pydantic import model_validator

from ..constants import MX_CHOICES_LITERAL, DEFAULT_MX
from ..search.models import HmmerJob, Database
from ..search.schemas import (
    PyhmmerAlignmentSchema,
    AlignmentDisplay,
    DomainSchema,
)

MXChoicesType = Literal[MX_CHOICES_LITERAL]


class TaskResultSchema(ModelSchema):
    result: Optional[List[dict]] = Field(default_factory=list)

    @field_validator("result", mode="before")
    @classmethod
    def parse_result(cls, value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return []
        return value

    class Meta:
        model = TaskResult
        fields = ["status", "date_created", "date_done", "result"]


class DatabaseResponseSchema(ModelSchema):
    class Meta:
        model = Database
        fields = "__all__"


class SearchResponseSchema(Schema):
    id: UUID4


class JobDetailsResponseSchema(ModelSchema):
    task: Optional[TaskResultSchema] = None
    database: Optional[DatabaseResponseSchema] = None
    status: str

    class Meta:
        model = HmmerJob
        exclude = ["algo"]


class JobsResponseSchema(ModelSchema):
    task: TaskResultSchema

    class Meta:
        model = HmmerJob
        fields = ["id", "algo"]


class HmmerJobStatusSchema(Schema):
    id: UUID4 = Field(..., description="The id of the job")
    status: str = Field(..., description="The status of the job")
    result_url: Optional[str] = Field(
        ..., description="URL to get the result of the job"
    )
    error_message: Optional[str] = Field(
        ..., description="The error message of the job"
    )


class CutOffSchema(Schema):
    threshold: Literal["evalue", "bitscore"] = "evalue"
    incE: Optional[float] = Field(0.01, gt=0, le=10)
    incdomE: Optional[float] = Field(0.03, gt=0, le=10)
    E: Optional[float] = Field(1.0, gt=0, le=10)
    domE: Optional[float] = Field(1.0, gt=0, le=10)
    incT: Optional[float] = Field(25.0, gt=0)
    incdomT: Optional[float] = Field(22.0, gt=0)
    T: Optional[float] = Field(7.0, gt=0)
    domT: Optional[float] = Field(5.0, gt=0)

    @model_validator(mode="after")
    def clean_threshold_fields(self):
        if self.threshold == "evalue":
            self.incT = None
            self.incdomT = None
            self.T = None
            self.domT = None
        else:
            self.incE = None
            self.incdomE = None
            self.E = None
            self.domE = None
        return self


class GapPenaltiesSchema(Schema):
    popen: Optional[float] = Field(0.02, ge=0, lt=0.5)
    pextend: Optional[float] = Field(0.4, ge=0, lt=1.0)
    mx: Optional[MXChoicesType] = Field(
        default=DEFAULT_MX, description="Substitution matrix"
    )


class ResultQuerySchema(Schema):
    page: int = Field(default=1, gt=0)
    page_size: int = Field(default=50, gt=0)
    taxonomy_ids: Optional[List[int]] = Field(default=None)
    architecture: Optional[str] = Field(default=None)
    with_domains: Optional[bool] = Field(default=False)


class DomainDetailsResponseSchema(Schema):
    target: str = Field(..., description="Target sequence name")
    domains: Optional[List[DomainSchema]] = Field(
        None, description="List of domains with alignment data"
    )


class AlignmentDetailsResponseSchema(Schema):
    """Response schema for detailed alignment information"""

    status: str = Field(..., description="Status of the request")
    target: str = Field(..., description="Target sequence name")
    domain_index: Optional[int] = Field(None, description="Index of the domain")
    alignment: Optional[PyhmmerAlignmentSchema] = Field(
        None, description="PyHMMER alignment data"
    )
    simple_alignment: Optional[AlignmentDisplay] = Field(
        None, description="Simple alignment display for UI"
    )
