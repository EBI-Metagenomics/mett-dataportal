from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class SpeciesSchema(BaseModel):
    scientific_name: str
    common_name: str
    acronym: str
    taxonomy_id: int

    model_config = ConfigDict(from_attributes=True)


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


class GeneAutocompleteResponseSchema(BaseModel):
    locus_tag: Optional[str] = None
    gene_name: Optional[str] = None
    alias: Optional[List[str]] = None
    isolate_name: Optional[str] = None
    species_scientific_name: Optional[str] = None
    species_acronym: Optional[str] = None
    product: Optional[str] = None
    kegg: Optional[List[str]] = None
    uniprot_id: Optional[str] = None
    pfam: Optional[List[str]] = None
    cog_id: Optional[str] = None
    interpro: Optional[List[str]] = None
    essentiality: Optional[str] = "Unknown"

    model_config = ConfigDict(from_attributes=True)

class EssentialityTagSchema(BaseModel):
    name: str
    label: str

    model_config = ConfigDict(from_attributes=True)

class DBXRefSchema(BaseModel):
    db: str
    ref: str

    model_config = ConfigDict(from_attributes=True)

class GeneResponseSchema(BaseModel):
    locus_tag: Optional[str] = None
    gene_name: Optional[str] = None
    alias: Optional[List[str]] = None
    product: Optional[str] = None
    start_position: Optional[int] = None
    end_position: Optional[int] = None
    seq_id: Optional[str] = None
    isolate_name: Optional[str] = None
    uniprot_id: Optional[str] = None
    essentiality: Optional[str] = "Unknown"
    cog_funcats: Optional[List[str]] = None
    cog_id: Optional[str] = None
    kegg: Optional[List[str]] = None
    pfam: Optional[List[str]] = None
    interpro: Optional[List[str]] = None
    ec_number: Optional[str] = None
    dbxref: Optional[List[DBXRefSchema]] = None

    model_config = ConfigDict(from_attributes=True)


class BasePaginationSchema(BaseModel):
    page_number: int
    num_pages: int
    has_previous: bool
    has_next: bool
    total_results: int

    model_config = ConfigDict(from_attributes=True)


class GenomePaginationSchema(BasePaginationSchema):
    results: List[GenomeResponseSchema]


class GenePaginationSchema(BasePaginationSchema):
    results: List[GeneResponseSchema]


class EssentialityByContigSchema(BaseModel):
    locus_tag: str
    start: Optional[int]
    end: Optional[int]
    essentiality: str


__all__ = [
    "StrainSuggestionSchema",
    "GeneAutocompleteResponseSchema",
    "ContigSchema",
    "GenomeResponseSchema",
    "GenePaginationSchema",
    "GeneResponseSchema",
    "GenomePaginationSchema",
    "SpeciesSchema",
]
