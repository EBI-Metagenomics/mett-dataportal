from typing import Optional, List, Dict

from pydantic import BaseModel, ConfigDict


class SpeciesSchema(BaseModel):
    id: int
    scientific_name: str
    common_name: str
    acronym: str

    model_config = ConfigDict(from_attributes=True)


class StrainSuggestionSchema(BaseModel):
    strain_id: int
    isolate_name: str
    assembly_name: str

    model_config = ConfigDict(from_attributes=True)


class ContigSchema(BaseModel):
    seq_id: str
    length: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class GenomeResponseSchema(BaseModel):
    id: int
    species: SpeciesSchema
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
    gene_id: int
    gene_name: Optional[str]
    strain_name: str
    product: Optional[str] = None
    locus_tag: Optional[str] = None
    kegg: Optional[str] = None
    pfam: Optional[str] = None
    interpro: Optional[str] = None
    dbxref: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class EssentialityTagSchema(BaseModel):
    id: int
    name: str
    label: str

    model_config = ConfigDict(from_attributes=True)


class GeneEssentialitySchema(BaseModel):
    media: str
    essentiality: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class GeneResponseSchema(BaseModel):
    id: int
    seq_id: Optional[str] = None
    gene_name: Optional[str] = None
    description: Optional[str] = None
    strain_id: Optional[int] = None
    strain: Optional[str] = None
    assembly: Optional[str] = None
    locus_tag: Optional[str] = None
    cog: Optional[str] = None
    kegg: Optional[str] = None
    pfam: Optional[str] = None
    interpro: Optional[str] = None
    dbxref: Optional[str] = None
    ec_number: Optional[str] = None
    product: Optional[str] = None
    start_position: Optional[int] = None
    end_position: Optional[int] = None
    annotations: Optional[dict] = None
    essentiality_data: Optional[List[GeneEssentialitySchema]] = None

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


class EssentialityDataSchema(BaseModel):
    media: str
    essentiality: str


class EssentialityByContigSchema(BaseModel):
    locus_tag: str
    start: Optional[int]
    end: Optional[int]
    essentiality_data: List[EssentialityDataSchema]


__all__ = [
    "StrainSuggestionSchema",
    "GeneAutocompleteResponseSchema",
    "ContigSchema",
    "GenomeResponseSchema",
    "GenePaginationSchema",
    "GeneResponseSchema",
    "GenomePaginationSchema",
    "SpeciesSchema",
    "EssentialityDataSchema",
]
