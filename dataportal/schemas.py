from typing import Optional, List

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


class ContigSchema(BaseModel):
    seq_id: str
    length: Optional[int] = None


class SearchGenomeSchema(BaseModel):
    species: str
    id: int
    common_name: Optional[str]
    isolate_name: str
    assembly_name: Optional[str]
    assembly_accession: Optional[str]
    fasta_file: str
    gff_file: str
    fasta_url: str
    gff_url: str
    contigs: List[ContigSchema]


class TypeStrainSchema(BaseModel):
    id: int
    isolate_name: str
    assembly_name: Optional[str]
    assembly_accession: Optional[str]
    fasta_file: str
    gff_file: str


class GenomePaginationSchema(BaseModel):
    results: List[SearchGenomeSchema]
    page_number: int
    num_pages: int
    has_previous: bool
    has_next: bool
    total_results: int


class GeneAutocompleteResponseSchema(BaseModel):
    gene_id: int
    gene_name: Optional[str]
    strain_name: str


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

    model_config = ConfigDict(from_attributes=True)


class GenePaginationSchema(BaseModel):
    results: List[GeneResponseSchema]
    page_number: int
    num_pages: int
    has_previous: bool
    has_next: bool
    total_results: int


__all__ = [
    "StrainSuggestionSchema",
    "GeneAutocompleteResponseSchema",
    "ContigSchema",
    "SearchGenomeSchema",
    "TypeStrainSchema",
    "GenePaginationSchema",
    "GeneResponseSchema",
    "GenomePaginationSchema",
    "SpeciesSchema",
]
