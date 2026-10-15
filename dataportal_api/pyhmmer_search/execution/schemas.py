"""Values passed between search steps.

These are internal models. The HTTP contract stays in ``search.schemas``.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from ..constants import DEFAULT_THRESHOLD, PIPELINE_FIELDS
from ..membership import resolve_scope


class SearchScope(BaseModel):
    """Which sequences in the single protein database a job may search."""

    species: list[str] = Field(default_factory=list)
    type_only: bool = False
    isolate: str = ""

    @classmethod
    def from_job(cls, job) -> "SearchScope":
        raw_species = getattr(job, "species", None)
        raw_type_only = getattr(job, "type_only", False)
        raw_isolate = getattr(job, "isolate", "")
        species, type_only, isolate = resolve_scope(
            getattr(job, "database", "") or "",
            raw_species if isinstance(raw_species, list) else [],
            raw_type_only if isinstance(raw_type_only, bool) else False,
            raw_isolate if isinstance(raw_isolate, str) else "",
        )
        return cls(species=species, type_only=type_only, isolate=isolate)


class PipelineParameters(BaseModel):
    """HMMER reporting thresholds and gap penalties taken from a job."""

    E: Optional[float] = None
    domE: Optional[float] = None
    incE: Optional[float] = None
    incdomE: Optional[float] = None
    T: Optional[float] = None
    domT: Optional[float] = None
    incT: Optional[float] = None
    incdomT: Optional[float] = None
    popen: Optional[float] = None
    pextend: Optional[float] = None
    threshold: str = DEFAULT_THRESHOLD
    mx: Optional[str] = None

    @classmethod
    def from_job(cls, job) -> "PipelineParameters":
        return cls(
            E=job.E,
            domE=job.domE,
            incE=job.incE,
            incdomE=job.incdomE,
            T=job.T,
            domT=job.domT,
            incT=job.incT,
            incdomT=job.incdomT,
            popen=job.popen,
            pextend=job.pextend,
            threshold=job.threshold or DEFAULT_THRESHOLD,
            mx=job.mx,
        )

    def pipeline_kwargs(self) -> dict[str, float]:
        values = self.model_dump()
        return {name: values[name] for name in PIPELINE_FIELDS if values[name] is not None}

    def builder_kwargs(self) -> dict[str, float]:
        values = {}
        if self.popen is not None:
            values["popen"] = self.popen
        if self.pextend is not None:
            values["pextend"] = self.pextend
        return values


class QuerySequence(BaseModel):
    """One protein sequence parsed from the job's FASTA input."""

    name: str
    sequence: str

    @classmethod
    def parse_fasta(cls, text: str) -> "QuerySequence":
        lines = (text or "").strip().splitlines()
        if not lines or not lines[0].startswith(">") or len(lines) < 2:
            raise ValueError("Invalid FASTA input format for query.")
        return cls(name=lines[0].lstrip(">"), sequence="".join(lines[1:]))
