import io
import json
import logging
from typing import Literal, Optional, List, Tuple

from django_celery_results.models import TaskResult
from ninja import ModelSchema
from ninja import Schema, Field
from pydantic import UUID4, ValidationInfo, field_validator
from pydantic import model_validator
from pydantic_core import PydanticCustomError
from pyhmmer.easel import SequenceFile

from .models import HmmerJob, Database
from ..constants import MX_CHOICES_LITERAL, DEFAULT_MX

MXChoicesType = Literal[MX_CHOICES_LITERAL]

logger = logging.getLogger(__name__)


class PyhmmerAlignmentSchema(Schema):
    """Schema for pyhmmer.plan7.Alignment data"""

    hmm_name: str = Field(..., description="Name of the query HMM")
    hmm_accession: Optional[str] = Field(None, description="Accession of the query HMM")
    hmm_from: int = Field(..., description="Start coordinate in the query HMM")
    hmm_to: int = Field(..., description="End coordinate in the query HMM")
    hmm_length: Optional[int] = Field(
        None, description="Length of the query HMM in the alignment"
    )
    hmm_sequence: str = Field(
        ..., description="Sequence of the query HMM in the alignment"
    )

    target_name: str = Field(..., description="Name of the target sequence")
    target_from: int = Field(..., description="Start coordinate in the target sequence")
    target_to: int = Field(..., description="End coordinate in the target sequence")
    target_length: Optional[int] = Field(
        None, description="Length of the target sequence in the alignment"
    )
    target_sequence: str = Field(
        ..., description="Sequence of the target sequence in the alignment"
    )

    identity_sequence: str = Field(
        ..., description="Identity sequence between query and target"
    )
    posterior_probabilities: Optional[str] = Field(
        None, description="Posterior probability annotation"
    )


class AlignmentDisplay(Schema):
    """Simple alignment display format for UI rendering"""

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
    """Enhanced domain schema with alignment support"""

    env_from: Optional[int] = Field(
        None, description="Start coordinate of domain envelope"
    )
    env_to: Optional[int] = Field(None, description="End coordinate of domain envelope")
    bitscore: float = Field(..., description="Bit score of the domain")
    ievalue: float = Field(..., description="Independent E-value of the domain")
    cevalue: Optional[float] = Field(
        None, description="Conditional E-value of the domain"
    )
    bias: Optional[float] = Field(None, description="Bias score contribution")
    strand: Optional[str] = Field(
        None, description="Strand where domain is located (+/-)"
    )
    is_significant: bool = Field(..., description="Whether this domain is significant")

    # Alignment data
    alignment: Optional[PyhmmerAlignmentSchema] = Field(
        None, description="PyHMMER alignment data"
    )
    alignment_display: Optional[AlignmentDisplay] = Field(
        None, description="Simple alignment display for UI"
    )


class HitSchema(Schema):
    """Enhanced hit schema with better field descriptions"""

    target: str = Field(..., description="Target sequence name")
    description: str = Field(..., description="Target sequence description")
    evalue: str = Field(..., description="E-value formatted as string")
    score: str = Field(..., description="Bit score formatted as string")
    sequence: Optional[str] = Field(None, description="Target sequence")
    bias: Optional[float] = Field(None, description="Bias score contribution")
    num_hits: Optional[int] = Field(None, description="Total number of hits")
    num_significant: Optional[int] = Field(
        None, description="Number of significant hits"
    )
    is_significant: bool = Field(
        ..., description="Whether this individual hit is significant"
    )
    domains: List[DomainSchema] = Field(..., description="List of domains for this hit")


# Response Schemas
class MessageSchema(Schema):
    message: str


class SearchRequestSchema(ModelSchema):
    database: str = Field(..., description="Database identifier (consolidated or isolate-specific)")
    threshold: Literal["evalue", "bitscore"]
    threshold_value: float
    input: str
    mx: Optional[MXChoicesType] = Field(
        default=DEFAULT_MX, description="Substitution matrix"
    )

    # E-value parameters
    E: Optional[float] = Field(None, description="Report E-values - Sequence")
    domE: Optional[float] = Field(None, description="Report E-values - Hit")
    incE: Optional[float] = Field(None, description="Significance E-values - Sequence")
    incdomE: Optional[float] = Field(None, description="Significance E-values - Hit")

    # Bit score parameters
    T: Optional[float] = Field(None, description="Report Bit scores - Sequence")
    domT: Optional[float] = Field(None, description="Report Bit scores - Hit")
    incT: Optional[float] = Field(
        None, description="Significance Bit scores - Sequence"
    )
    incdomT: Optional[float] = Field(None, description="Significance Bit scores - Hit")

    # Gap penalties
    popen: float = Field(default=0.02, ge=0.0, description="Gap open penalty")
    pextend: float = Field(default=0.4, ge=0.0, description="Gap extend penalty")

    @field_validator("input", mode="after", check_fields=False)
    @classmethod
    def check_input(cls, value: str, info: ValidationInfo):
        """Validate input sequence format and content"""
        if not value or not value.strip():
            raise PydanticCustomError("invalid_input", "Input sequence cannot be empty")

        lines = value.strip().splitlines()
        if not lines:
            raise PydanticCustomError("invalid_input", "Input sequence cannot be empty")

        # Check if first line starts with '>' (FASTA header)
        if not lines[0].startswith(">"):
            raise PydanticCustomError(
                "invalid_input",
                "Input must be in FASTA format. First line must start with '>' followed by a sequence identifier. "
                "Example: >my_protein\nMSEIDHVGLWNRCLEIIRDNVPEQTYKTWFLPIIPLKYEDKTLV",
            )

        # Check if we have sequence data after header
        if len(lines) < 2:
            raise PydanticCustomError(
                "invalid_input",
                "Input must contain sequence data after the header line",
            )

        # Extract and validate sequence
        sequence_lines = lines[1:]
        sequence = "".join(sequence_lines).strip()

        if not sequence:
            raise PydanticCustomError("invalid_input", "Sequence data cannot be empty")

        # Check sequence length
        if len(sequence) < 10:
            raise PydanticCustomError(
                "invalid_input", "Sequence must be at least 10 characters long"
            )

        sequence_upper = sequence.upper()

        protein_chars = set("ACDEFGHIKLMNPQRSTVWY*")
        dna_chars = set("ACGTN")
        rna_chars = set("ACGUN")

        seq_strict = "".join(
            c for c in sequence_upper if c not in {" ", "\n", "\r", "\t", "-"}
        )

        # if all characters are DNA or all are RNA, reject
        if seq_strict and all(c in dna_chars for c in seq_strict):
            raise PydanticCustomError(
                "invalid_input",
                "DNA sequence detected. Please provide a protein sequence in FASTA format. If you have a DNA sequence, translate it to protein first.",
            )
        if seq_strict and all(c in rna_chars for c in seq_strict):
            raise PydanticCustomError(
                "invalid_input",
                "RNA sequence detected. Please provide a protein sequence in FASTA format. If you have an RNA sequence, translate it to protein first.",
            )

        # Count character types
        protein_count = sum(1 for c in sequence_upper if c in protein_chars)
        dna_count = sum(1 for c in sequence_upper if c in dna_chars)
        rna_count = sum(1 for c in sequence_upper if c in rna_chars)
        total_chars = len(sequence_upper)

        # Calculate percentages
        protein_pct = protein_count / total_chars if total_chars > 0 else 0
        dna_pct = dna_count / total_chars if total_chars > 0 else 0
        rna_pct = rna_count / total_chars if total_chars > 0 else 0

        # Check for invalid characters
        invalid_chars = (
            set(sequence_upper)
            - protein_chars
            - dna_chars
            - rna_chars
            - {" ", "\n", "\r", "\t"}
        )
        if invalid_chars:
            raise PydanticCustomError(
                "invalid_input",
                f"Sequence contains invalid characters: {', '.join(sorted(invalid_chars))}. "
                f"Valid characters are: A-Z (amino acids), A/C/G/T/N (DNA), A/C/G/U/N (RNA)",
            )

        if protein_pct >= 0.8:
            if protein_pct < 1.0:
                logger.warning(
                    f"Protein sequence contains some non-standard amino acids. Protein percentage: {protein_pct:.1%}"
                )
        elif dna_pct >= 0.8:
            raise PydanticCustomError(
                "invalid_input",
                "DNA sequence detected. Please provide a protein sequence in FASTA format. If you have a DNA sequence, translate it to protein first.",
            )
        elif rna_pct >= 0.8:
            raise PydanticCustomError(
                "invalid_input",
                "RNA sequence detected. Please provide a protein sequence in FASTA format. If you have an RNA sequence, translate it to protein first.",
            )
        else:
            # Mixed or unclear sequence type
            raise PydanticCustomError(
                "invalid_input",
                "Sequence type unclear. PyHMMER requires protein sequences. "
                f"Detected: {protein_pct:.1%} protein, {dna_pct:.1%} DNA, {rna_pct:.1%} RNA. "
                "Please provide a clear protein sequence.",
            )

        # Try to validate with PyHMMER's SequenceFile
        try:
            with SequenceFile(io.BytesIO(value.encode())) as fh:
                fh.guess_alphabet()
        except Exception as e:
            raise PydanticCustomError(
                "invalid_input", f"PyHMMER validation failed: {str(e)}"
            )

        return value

    @field_validator("database", mode="after")
    @classmethod
    def validate_database(cls, value: str):
        """Validate database identifier"""
        # Check if it's a valid consolidated database
        valid_consolidated = [
            "bu_type_strains", "bu_all", "pv_type_strains", "pv_all", 
            "bu_pv_type_strains", "bu_pv_all"
        ]
        
        if value in valid_consolidated:
            return value
        
        # Check if it's a valid isolate-specific database
        if value.startswith('isolate_'):
            isolate_name = value.replace('isolate_', '')
            # Basic validation for isolate name format
            if isolate_name and (isolate_name.startswith('BU_') or isolate_name.startswith('PV_')):
                return value
            else:
                raise PydanticCustomError(
                    "invalid_database",
                    "Isolate-specific database must have format 'isolate_BU_XXXXX' or 'isolate_PV_XXXXX'"
                )
        
        # If neither, it's invalid
        raise PydanticCustomError(
            "invalid_database",
            f"Database must be one of: {', '.join(valid_consolidated)} or isolate-specific format 'isolate_BU_XXXXX'/'isolate_PV_XXXXX'"
        )

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
    incE: Optional[float] = Field(0.01, ge=0, le=100.0)
    incdomE: Optional[float] = Field(0.03, ge=0, le=100.0)
    E: Optional[float] = Field(1.0, ge=0, le=100.0)
    domE: Optional[float] = Field(1.0, ge=0, le=100.0)
    incT: Optional[float] = Field(25.0, ge=0.0, le=1000.0)
    incdomT: Optional[float] = Field(22.0, ge=0.0, le=1000.0)
    T: Optional[float] = Field(7.0, ge=0.0, le=1000.0)
    domT: Optional[float] = Field(5.0, ge=0.0, le=1000.0)

    @model_validator(mode="after")
    def clean_threshold_fields(self):
        if self.threshold == "evalue":
            self.incT = self.incdomT = self.T = self.domT = None
            if self.E and self.incE and self.incE > self.E:
                raise ValueError("incE should be ≤ E")
            if self.domE and self.incdomE and self.incdomE > self.domE:
                raise ValueError("incdomE should be ≤ domE")
        else:
            self.incE = self.incdomE = self.E = self.domE = None
            if self.T and self.incT and self.incT < self.T:
                raise ValueError("incT should be ≥ T")
            if self.domT and self.incdomT and self.incdomT < self.domT:
                raise ValueError("incdomT should be ≥ domT")
        return self


class GapPenaltiesSchema(Schema):
    popen: Optional[float] = Field(0.02, ge=0, lt=0.5)
    pextend: Optional[float] = Field(0.4, ge=0, lt=1.0)
    mx: Optional[MXChoicesType] = Field(
        default=DEFAULT_MX, description="Substitution matrix"
    )


class ResultQuerySchema(Schema):
    page: int = Field(default=1, gt=0)
    page_size: int = Field(default=20, gt=0)
    taxonomy_ids: Optional[List[int]] = Field(default=None)
    architecture: Optional[str] = Field(default=None)
    with_domains: Optional[bool] = Field(default=False)


class DomainDetailsResponseSchema(Schema):
    status: str = Field(..., description="Status of the request")
    target: str = Field(..., description="Target sequence name")
    domains: Optional[List[DomainSchema]] = Field(
        None, description="List of domains with alignment data"
    )


class AlignmentDetailsResponseSchema(Schema):
    status: str = Field(..., description="Status of the request")
    target: str = Field(..., description="Target sequence name")
    domain_index: Optional[int] = Field(None, description="Index of the domain")
    alignment: Optional[PyhmmerAlignmentSchema] = Field(
        None, description="PyHMMER alignment data"
    )
    simple_alignment: Optional[AlignmentDisplay] = Field(
        None, description="Simple alignment display for UI"
    )
