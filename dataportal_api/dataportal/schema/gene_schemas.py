from typing import Optional, List

from pydantic import BaseModel, ConfigDict
from pydantic import Field

from dataportal.schema.base_schemas import BasePaginationSchema
from dataportal.utils.constants import DEFAULT_PER_PAGE_CNT, DEFAULT_SORT, DEFAULT_FACET_LIMIT


class GeneAutocompleteQuerySchema(BaseModel):
    """Schema for gene autocomplete endpoint query parameters."""
    query: str = Field(
        ...,
        description="Free-text input to search gene names, locus tags, or annotations."
    )
    filter: Optional[str] = Field(
        None,
        description="Optional semicolon-separated gene filters, e.g., 'essentiality:essential_liquid;interpro:IPR035952'."
    )
    limit: int = Field(
        DEFAULT_PER_PAGE_CNT,
        description="Maximum number of gene suggestions to return."
    )
    species_acronym: Optional[str] = Field(
        None,
        description="Optional species acronym filter (e.g., 'BU', 'PV')."
    )
    isolates: Optional[str] = Field(
        None,
        description="Comma-separated list of isolate names to restrict the search scope."
    )


class GeneSearchQuerySchema(BaseModel):
    """Schema for basic gene search endpoint."""
    query: str = Field(
        "",
        description="Free-text search term to match against gene names or locus tags."
    )
    page: int = Field(
        1,
        description="Page number for pagination (1-based)."
    )
    per_page: int = Field(
        DEFAULT_PER_PAGE_CNT,
        description="Number of genes to return per page."
    )
    sort_field: Optional[str] = Field(
        None,
        description="Field to sort results by (e.g., 'gene_name', 'isolate_name')."
    )
    sort_order: Optional[str] = Field(
        DEFAULT_SORT,
        description="Sort order: 'asc' or 'desc'."
    )


class GeneFacetedSearchQuerySchema(BaseModel):
    """Schema for faceted gene search filtering by functional/metadata facets."""
    query: Optional[str] = Field(
        None,
        description="Free-text search across gene fields such as gene name and product."
    )
    species_acronym: Optional[str] = Field(
        None,
        description="Species acronym filter (e.g., 'BU', 'PV')."
    )
    essentiality: Optional[str] = Field(
        None,
        description="Filter by essentiality status, e.g., 'essential'."
    )
    isolates: Optional[str] = Field(
        "",
        description="Comma-separated list of isolate names to filter."
    )
    cog_id: Optional[str] = Field(
        None,
        description="Comma-separated list of COG IDs to filter."
    )
    cog_funcats: Optional[str] = Field(
        None,
        description="Comma-separated list of COG functional categories to filter."
    )
    kegg: Optional[str] = Field(
        None,
        description="KEGG pathway or gene ID to filter."
    )
    go_term: Optional[str] = Field(
        None,
        description="GO term ID or label to filter."
    )
    pfam: Optional[str] = Field(
        None,
        description="Pfam domain ID to filter."
    )
    interpro: Optional[str] = Field(
        None,
        description="InterPro ID to filter."
    )
    has_amr_info: Optional[bool] = Field(
        None,
        description="Filter genes that have associated AMR information."
    )
    pfam_operator: Optional[str] = Field(
        "OR",
        description="Logical operator ('AND'/'OR') for Pfam filtering."
    )
    interpro_operator: Optional[str] = Field(
        "OR",
        description="Logical operator ('AND'/'OR') for InterPro filtering."
    )
    cog_id_operator: Optional[str] = Field(
        "OR",
        description="Logical operator ('AND'/'OR') for COG ID filtering."
    )
    cog_funcats_operator: Optional[str] = Field(
        "OR",
        description="Logical operator ('AND'/'OR') for COG functional categories filtering."
    )
    kegg_operator: Optional[str] = Field(
        "OR",
        description="Logical operator ('AND'/'OR') for KEGG filtering."
    )
    go_term_operator: Optional[str] = Field(
        "OR",
        description="Logical operator ('AND'/'OR') for GO term filtering."
    )
    limit: int = Field(
        DEFAULT_FACET_LIMIT,
        description="Maximum number of genes to return."
    )


class GeneAdvancedSearchQuerySchema(BaseModel):
    """Schema for advanced gene search across multiple genomes/species with filters."""
    isolates: str = Field(
        "",
        description="Comma-separated list of isolate names to filter."
    )
    species_acronym: Optional[str] = Field(
        None,
        description="Species acronym to filter (e.g., 'BU', 'PV')."
    )
    query: str = Field(
        "",
        description="Free-text search string for gene names, locus tags, or annotations."
    )
    filter: Optional[str] = Field(
        None,
        description="Additional gene filter, e.g., 'pfam:PF07715;interpro:IPR012910'."
    )
    filter_operators: Optional[str] = Field(
        None,
        description="Logical operators for filters, e.g., 'pfam:AND;interpro:OR'."
    )
    page: int = Field(
        1,
        description="Page number for pagination (1-based)."
    )
    per_page: int = Field(
        DEFAULT_PER_PAGE_CNT,
        description="Number of genes to return per page."
    )
    sort_field: Optional[str] = Field(
        None,
        description="Field to sort results by, e.g., 'gene_name', 'isolate_name'."
    )
    sort_order: Optional[str] = Field(
        DEFAULT_SORT,
        description="Sort order: 'asc' or 'desc'."
    )


class GeneDownloadTSVQuerySchema(BaseModel):
    """Schema for downloading genes as TSV with filtering and sorting."""
    isolates: str = Field(
        "",
        description="Comma-separated list of isolate names to filter."
    )
    species_acronym: Optional[str] = Field(
        None,
        description="Species acronym filter (e.g., 'BU', 'PV')."
    )
    query: str = Field(
        "",
        description="Free-text search string for gene names, locus tags, or annotations."
    )
    filter: Optional[str] = Field(
        None,
        description="Additional gene filter, e.g., 'pfam:PF07715;interpro:IPR012910'."
    )
    filter_operators: Optional[str] = Field(
        None,
        description="Logical operators for filters, e.g., 'pfam:AND;interpro:OR'."
    )
    sort_field: Optional[str] = Field(
        None,
        description="Field to sort results by."
    )
    sort_order: Optional[str] = Field(
        DEFAULT_SORT,
        description="Sort order: 'asc' or 'desc'."
    )


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


class AMRSchema(BaseModel):
    gene_symbol: Optional[str] = None
    sequence_name: Optional[str] = None
    scope: Optional[str] = None
    element_type: Optional[str] = None
    element_subtype: Optional[str] = None
    drug_class: Optional[str] = None
    drug_subclass: Optional[str] = None
    uf_keyword: Optional[List[str]] = None
    uf_ecnumber: Optional[str] = None


class GeneQuery(BaseModel):
    species: str | None = None
    essentiality: str | None = None
    amr: bool | None = None
    function: str | None = None
    cog_category: str | None = None


class GeneResponseSchema(BaseModel):
    locus_tag: Optional[str] = None
    gene_name: Optional[str] = None
    alias: Optional[List[str]] = None
    product: Optional[str] = None
    start_position: Optional[int] = None
    end_position: Optional[int] = None
    seq_id: Optional[str] = None
    isolate_name: Optional[str] = None
    species_scientific_name: Optional[str] = None
    species_acronym: Optional[str] = None
    uniprot_id: Optional[str] = None
    essentiality: Optional[str] = "Unknown"
    cog_funcats: Optional[List[str]] = None
    cog_id: Optional[str] = None
    kegg: Optional[List[str]] = None
    pfam: Optional[List[str]] = None
    interpro: Optional[List[str]] = None
    ec_number: Optional[str] = None
    dbxref: Optional[List[DBXRefSchema]] = None
    eggnog: Optional[str] = None
    amr: Optional[List[AMRSchema]] = None
    has_amr_info: Optional[bool] = None
    model_config = ConfigDict(from_attributes=True)


class GeneProteinSeqSchema(BaseModel):
    locus_tag: Optional[str] = None
    protein_sequence: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class GenePaginationSchema(BasePaginationSchema):
    results: List[GeneResponseSchema]


class EssentialityByContigSchema(BaseModel):
    locus_tag: str
    start: Optional[int]
    end: Optional[int]
    essentiality: str


__all__ = [
    "GeneAutocompleteResponseSchema",
    "GenePaginationSchema",
    "GeneResponseSchema",
]
