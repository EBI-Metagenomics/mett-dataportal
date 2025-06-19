import io
import json
from typing import Literal, Optional, List, Tuple

from django_celery_results.models import TaskResult
from ninja import ModelSchema
from ninja import Schema, Field
from pydantic import UUID4, ValidationInfo, field_validator
from pydantic import model_validator
from pydantic_core import PydanticCustomError
from pyhmmer.easel import SequenceFile

from .models import HmmerJob, Database


# Enhanced Alignment Models based on pyhmmer.plan7.Alignment
class PyhmmerAlignmentSchema(Schema):
    """Schema for pyhmmer.plan7.Alignment data"""
    hmm_name: str = Field(..., description="Name of the query HMM")
    hmm_accession: Optional[str] = Field(None, description="Accession of the query HMM")
    hmm_from: int = Field(..., description="Start coordinate in the query HMM")
    hmm_to: int = Field(..., description="End coordinate in the query HMM")
    hmm_length: Optional[int] = Field(None, description="Length of the query HMM in the alignment")
    hmm_sequence: str = Field(..., description="Sequence of the query HMM in the alignment")

    target_name: str = Field(..., description="Name of the target sequence")
    target_from: int = Field(..., description="Start coordinate in the target sequence")
    target_to: int = Field(..., description="End coordinate in the target sequence")
    target_length: Optional[int] = Field(None, description="Length of the target sequence in the alignment")
    target_sequence: str = Field(..., description="Sequence of the target sequence in the alignment")

    identity_sequence: str = Field(..., description="Identity sequence between query and target")
    posterior_probabilities: Optional[str] = Field(None, description="Posterior probability annotation")


class LegacyAlignmentDisplay(Schema):
    """Legacy alignment display for backward compatibility"""
    hmmfrom: int
    hmmto: int
    sqfrom: int
    sqto: int
    model: str
    aseq: str
    mline: str
    ppline: Optional[str] = None
    identity: Tuple[float, int]
    similarity: Tuple[float, int]


class DomainSchema(Schema):
    """Enhanced domain schema with both new and legacy alignment support"""
    env_from: Optional[int] = Field(None, description="Start coordinate of domain envelope")
    env_to: Optional[int] = Field(None, description="End coordinate of domain envelope")
    bitscore: float = Field(..., description="Bit score of the domain")
    ievalue: float = Field(..., description="Independent E-value of the domain")
    cevalue: Optional[float] = Field(None, description="Conditional E-value of the domain")
    bias: Optional[float] = Field(None, description="Bias score contribution")
    strand: Optional[str] = Field(None, description="Strand where domain is located (+/-)")

    # Alignment data
    alignment: Optional[PyhmmerAlignmentSchema] = Field(None, description="PyHMMER alignment data")
    alignment_display: Optional[LegacyAlignmentDisplay] = Field(None, description="Legacy alignment display")


class HitSchema(Schema):
    """Enhanced hit schema with better field descriptions"""
    target: str = Field(..., description="Target sequence name")
    description: str = Field(..., description="Target sequence description")
    evalue: str = Field(..., description="E-value formatted as string")
    score: str = Field(..., description="Bit score formatted as string")
    num_hits: Optional[int] = Field(None, description="Total number of hits")
    num_significant: Optional[int] = Field(None, description="Number of significant hits")
    domains: List[DomainSchema] = Field(..., description="List of domains for this hit")


# Response Schemas
class MessageSchema(Schema):
    message: str


class SearchRequestSchema(ModelSchema):
    database: Literal[tuple(HmmerJob.DbChoices.values)]
    threshold: Literal["evalue", "bitscore"]
    threshold_value: float
    input: str
    mx: Optional[
        Literal["BLOSUM62", "BLOSUM45", "BLOSUM90", "PAM30", "PAM70", "PAM250"]
    ] = "BLOSUM62"
    
    # E-value parameters
    E: Optional[float] = Field(None, description="Report E-values - Sequence")
    domE: Optional[float] = Field(None, description="Report E-values - Hit")
    incE: Optional[float] = Field(None, description="Significance E-values - Sequence")
    incdomE: Optional[float] = Field(None, description="Significance E-values - Hit")
    
    # Bit score parameters
    T: Optional[float] = Field(None, description="Report Bit scores - Sequence")
    domT: Optional[float] = Field(None, description="Report Bit scores - Hit")
    incT: Optional[float] = Field(None, description="Significance Bit scores - Sequence")
    incdomT: Optional[float] = Field(None, description="Significance Bit scores - Hit")
    
    # Gap penalties
    popen: Optional[float] = Field(None, description="Gap penalties - Open")
    pextend: Optional[float] = Field(None, description="Gap penalties - Extend")

    @field_validator("input", mode="after", check_fields=False)
    @classmethod
    def check_input(cls, value: str, info: ValidationInfo):
        try:
            with SequenceFile(io.BytesIO(value.encode())) as fh:
                fh.guess_alphabet()
            return value
        except Exception:
            raise PydanticCustomError("invalid_input", "Sequence is not valid")

    class Meta:
        model = HmmerJob
        exclude = ["id", "task", "algo"]


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


class HmmerJobCreatedSchema(Schema):
    id: UUID4 = Field(..., description="The id of the job")
    status: str = Field(..., description="The status of the job")
    status_url: str = Field(..., description="URL to get the status of the job")


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
    mx: Optional[
        Literal["BLOSUM62", "BLOSUM45", "BLOSUM90", "PAM30", "PAM70", "PAM250"]
    ] = "BLOSUM62"


class ResultQuerySchema(Schema):
    page: int = Field(default=1, gt=0)
    page_size: int = Field(default=50, gt=0)
    taxonomy_ids: Optional[List[int]] = Field(default=None)
    architecture: Optional[str] = Field(default=None)
    with_domains: Optional[bool] = Field(default=False)


class DomainDetailsResponseSchema(Schema):
    status: str = Field(..., description="Status of the request")
    target: str = Field(..., description="Target sequence name")
    domains: Optional[List[DomainSchema]] = Field(None, description="List of domains with alignment data")


class AlignmentDetailsResponseSchema(Schema):
    """Response schema for detailed alignment information"""
    status: str = Field(..., description="Status of the request")
    target: str = Field(..., description="Target sequence name")
    domain_index: Optional[int] = Field(None, description="Index of the domain")
    alignment: Optional[PyhmmerAlignmentSchema] = Field(None, description="PyHMMER alignment data")
    legacy_alignment: Optional[LegacyAlignmentDisplay] = Field(None, description="Legacy alignment display")
