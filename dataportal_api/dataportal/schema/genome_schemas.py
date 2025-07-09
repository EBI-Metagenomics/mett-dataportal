from typing import Optional, List

from pydantic import BaseModel, ConfigDict

from dataportal.schema.base_schemas import BasePaginationSchema


class StrainSuggestionSchema(BaseModel):
    isolate_name: str
    assembly_name: str

    model_config = ConfigDict(from_attributes=True)


class StrainMinSchema(BaseModel):
    isolate_name: str
    assembly_name: str

    model_config = ConfigDict(from_attributes=True)


class ContigSchema(BaseModel):
    seq_id: str
    length: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class GenomeResponseSchema(BaseModel):
    species_scientific_name: Optional[str] = None
    species_acronym: Optional[str] = None
    isolate_name: str
    assembly_name: Optional[str]
    assembly_accession: Optional[str]
    fasta_file: str
    gff_file: str
    fasta_url: str
    gff_url: str
    type_strain: bool
    contigs: List[ContigSchema]

    model_config = ConfigDict(from_attributes=True)


class GenomePaginationSchema(BasePaginationSchema):
    results: List[GenomeResponseSchema]


__all__ = [
    "StrainSuggestionSchema",
    "ContigSchema",
    "GenomeResponseSchema",
    "GenomePaginationSchema",
]
