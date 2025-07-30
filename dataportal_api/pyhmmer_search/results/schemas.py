import json
from typing import Literal

from django_celery_results.models import TaskResult
from ninja import Field, ModelSchema, Schema
from pydantic import UUID4, field_validator, model_validator

from ..constants import DEFAULT_MX, MX_CHOICES_LITERAL
from ..search.models import Database, HmmerJob
from ..search.schemas import (
    AlignmentDisplay,
    DomainSchema,
    PyhmmerAlignmentSchema,
)

MXChoicesType = Literal[MX_CHOICES_LITERAL]


class TaskResultSchema(ModelSchema):
    result: list[dict] | None = Field(default_factory=list)

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
    task: TaskResultSchema | None = None
    database: DatabaseResponseSchema | None = None
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
    result_url: str | None = Field(..., description="URL to get the result of the job")
    error_message: str | None = Field(..., description="The error message of the job")


class CutOffSchema(Schema):
    threshold: Literal["evalue", "bitscore"] = "evalue"
    incE: float | None = Field(0.01, gt=0, le=10)
    incdomE: float | None = Field(0.03, gt=0, le=10)
    E: float | None = Field(1.0, gt=0, le=10)
    domE: float | None = Field(1.0, gt=0, le=10)
    incT: float | None = Field(25.0, gt=0)
    incdomT: float | None = Field(22.0, gt=0)
    T: float | None = Field(7.0, gt=0)
    domT: float | None = Field(5.0, gt=0)

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
    popen: float | None = Field(0.02, ge=0, lt=0.5)
    pextend: float | None = Field(0.4, ge=0, lt=1.0)
    mx: MXChoicesType | None = Field(
        default=DEFAULT_MX, description="Substitution matrix"
    )


class ResultQuerySchema(Schema):
    page: int = Field(default=1, gt=0)
    page_size: int = Field(default=50, gt=0)
    taxonomy_ids: list[int] | None = Field(default=None)
    architecture: str | None = Field(default=None)
    with_domains: bool | None = Field(default=False)


class DomainDetailsResponseSchema(Schema):
    target: str = Field(..., description="Target sequence name")
    domains: list[DomainSchema] | None = Field(
        None, description="List of domains with alignment data"
    )


class AlignmentDetailsResponseSchema(Schema):
    """Response schema for detailed alignment information"""

    status: str = Field(..., description="Status of the request")
    target: str = Field(..., description="Target sequence name")
    domain_index: int | None = Field(None, description="Index of the domain")
    alignment: PyhmmerAlignmentSchema | None = Field(
        None, description="PyHMMER alignment data"
    )
    simple_alignment: AlignmentDisplay | None = Field(
        None, description="Simple alignment display for UI"
    )
