from pydantic import BaseModel, ConfigDict, Field

from dataportal.schema.base_schemas import BasePaginationSchema
from dataportal.utils.constants import (
    DEFAULT_FACET_LIMIT,
    DEFAULT_PER_PAGE_CNT,
    DEFAULT_SORT,
)


class GeneAutocompleteQuerySchema(BaseModel):
    """Schema for gene autocomplete endpoint query parameters."""

    query: str = Field(
        ...,
        description="Free-text input to search gene names, locus tags, or annotations.",
    )
    filter: str | None = Field(
        None,
        description="Optional semicolon-separated gene filters, e.g., 'essentiality:essential_liquid;interpro:IPR035952'.",
    )
    limit: int = Field(
        DEFAULT_PER_PAGE_CNT,
        description="Maximum number of gene suggestions to return.",
    )
    species_acronym: str | None = Field(
        None, description="Optional species acronym filter (e.g., 'BU', 'PV')."
    )
    isolates: str | None = Field(
        None,
        description="Comma-separated list of isolate names to restrict the search scope.",
    )


class GeneSearchQuerySchema(BaseModel):
    """Schema for basic gene search endpoint."""

    query: str = Field(
        "",
        description="Free-text search term to match against gene names or locus tags.",
    )
    page: int = Field(1, description="Page number for pagination (1-based).")
    per_page: int = Field(
        DEFAULT_PER_PAGE_CNT, description="Number of genes to return per page."
    )
    sort_field: str | None = Field(
        None,
        description="Field to sort results by (e.g., 'gene_name', 'isolate_name').",
    )
    sort_order: str | None = Field(
        DEFAULT_SORT, description="Sort order: 'asc' or 'desc'."
    )


class GeneFacetedSearchQuerySchema(BaseModel):
    """Schema for faceted gene search filtering by functional/metadata facets."""

    query: str | None = Field(
        None,
        description="Free-text search across gene fields such as gene name and product.",
    )
    species_acronym: str | None = Field(
        None, description="Species acronym filter (e.g., 'BU', 'PV')."
    )
    essentiality: str | None = Field(
        None, description="Filter by essentiality status, e.g., 'essential'."
    )
    isolates: str | None = Field(
        "", description="Comma-separated list of isolate names to filter."
    )
    cog_id: str | None = Field(
        None, description="Comma-separated list of COG IDs to filter."
    )
    cog_funcats: str | None = Field(
        None, description="Comma-separated list of COG functional categories to filter."
    )
    kegg: str | None = Field(None, description="KEGG pathway or gene ID to filter.")
    go_term: str | None = Field(None, description="GO term ID or label to filter.")
    pfam: str | None = Field(None, description="Pfam domain ID to filter.")
    interpro: str | None = Field(None, description="InterPro ID to filter.")
    has_amr_info: bool | None = Field(
        None, description="Filter genes that have associated AMR information."
    )
    pfam_operator: str | None = Field(
        "OR", description="Logical operator ('AND'/'OR') for Pfam filtering."
    )
    interpro_operator: str | None = Field(
        "OR", description="Logical operator ('AND'/'OR') for InterPro filtering."
    )
    cog_id_operator: str | None = Field(
        "OR", description="Logical operator ('AND'/'OR') for COG ID filtering."
    )
    cog_funcats_operator: str | None = Field(
        "OR",
        description="Logical operator ('AND'/'OR') for COG functional categories filtering.",
    )
    kegg_operator: str | None = Field(
        "OR", description="Logical operator ('AND'/'OR') for KEGG filtering."
    )
    go_term_operator: str | None = Field(
        "OR", description="Logical operator ('AND'/'OR') for GO term filtering."
    )
    limit: int = Field(
        DEFAULT_FACET_LIMIT, description="Maximum number of genes to return."
    )


class GeneAdvancedSearchQuerySchema(BaseModel):
    """Schema for advanced gene search across multiple genomes/species with filters."""

    isolates: str = Field(
        "", description="Comma-separated list of isolate names to filter."
    )
    species_acronym: str | None = Field(
        None, description="Species acronym to filter (e.g., 'BU', 'PV')."
    )
    query: str = Field(
        "",
        description="Free-text search string for gene names, locus tags, or annotations.",
    )
    filter: str | None = Field(
        None,
        description="Additional gene filter, e.g., 'pfam:PF07715;interpro:IPR012910'.",
    )
    filter_operators: str | None = Field(
        None, description="Logical operators for filters, e.g., 'pfam:AND;interpro:OR'."
    )
    page: int = Field(1, description="Page number for pagination (1-based).")
    per_page: int = Field(
        DEFAULT_PER_PAGE_CNT, description="Number of genes to return per page."
    )
    sort_field: str | None = Field(
        None, description="Field to sort results by, e.g., 'gene_name', 'isolate_name'."
    )
    sort_order: str | None = Field(
        DEFAULT_SORT, description="Sort order: 'asc' or 'desc'."
    )


class GeneDownloadTSVQuerySchema(BaseModel):
    """Schema for downloading genes as TSV with filtering and sorting."""

    isolates: str = Field(
        "", description="Comma-separated list of isolate names to filter."
    )
    species_acronym: str | None = Field(
        None, description="Species acronym filter (e.g., 'BU', 'PV')."
    )
    query: str = Field(
        "",
        description="Free-text search string for gene names, locus tags, or annotations.",
    )
    filter: str | None = Field(
        None,
        description="Additional gene filter, e.g., 'pfam:PF07715;interpro:IPR012910'.",
    )
    filter_operators: str | None = Field(
        None, description="Logical operators for filters, e.g., 'pfam:AND;interpro:OR'."
    )
    sort_field: str | None = Field(None, description="Field to sort results by.")
    sort_order: str | None = Field(
        DEFAULT_SORT, description="Sort order: 'asc' or 'desc'."
    )


class GeneAutocompleteResponseSchema(BaseModel):
    locus_tag: str | None = None
    gene_name: str | None = None
    alias: list[str] | None = None
    isolate_name: str | None = None
    species_scientific_name: str | None = None
    species_acronym: str | None = None
    product: str | None = None
    kegg: list[str] | None = None
    uniprot_id: str | None = None
    pfam: list[str] | None = None
    cog_id: list[str] | None = None
    interpro: list[str] | None = None
    essentiality: str | None = "Unknown"
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
    gene_symbol: str | None = None
    sequence_name: str | None = None
    scope: str | None = None
    element_type: str | None = None
    element_subtype: str | None = None
    drug_class: str | None = None
    drug_subclass: str | None = None
    uf_keyword: list[str] | None = None
    uf_ecnumber: str | None = None


class GeneQuery(BaseModel):
    species: str | None = None
    essentiality: str | None = None
    amr: bool | None = None
    function: str | None = None
    cog_category: str | None = None


class NaturalLanguageGeneQuery(BaseModel):
    """Comprehensive schema for natural language queries that maps directly to API parameters."""

    # Basic search parameters
    query: str | None = Field(
        None,
        description="Free-text search term for gene names, locus tags, or annotations",
    )
    species_acronym: str | None = Field(
        None, description="Species acronym filter (e.g., 'BU', 'PV')"
    )
    isolates: str | None = Field(
        None, description="Comma-separated list of isolate names"
    )

    # Essentiality and AMR filters
    essentiality: str | None = Field(
        None,
        description="Filter by essentiality status (e.g., 'essential', 'non_essential')",
    )
    has_amr_info: bool | None = Field(
        None, description="Filter genes that have associated AMR information"
    )

    # Functional annotation filters
    cog_id: str | None = Field(
        None, description="Comma-separated list of COG IDs to filter"
    )
    cog_funcats: str | None = Field(
        None, description="Comma-separated list of COG functional categories"
    )
    kegg: str | None = Field(None, description="KEGG pathway or gene ID to filter")
    go_term: str | None = Field(None, description="GO term ID or label to filter")
    pfam: str | None = Field(None, description="Pfam domain ID to filter")
    interpro: str | None = Field(None, description="InterPro ID to filter")

    # Additional filters
    filter: str | None = Field(None, description="Additional gene filter string")
    filter_operators: str | None = Field(
        None, description="Logical operators for filters"
    )

    # Pagination and sorting
    page: int = Field(1, description="Page number for pagination (1-based)")
    per_page: int = Field(50, description="Number of genes to return per page")
    sort_field: str | None = Field(None, description="Field to sort results by")
    sort_order: str = Field("asc", description="Sort order: 'asc' or 'desc'")

    # Limit for faceted search
    limit: int = Field(
        50, description="Maximum number of genes to return for faceted search"
    )

    # Backward compatibility fields (for simple queries)
    species: str | None = Field(
        None, description="Species filter (maps to species_acronym)"
    )
    amr: bool | None = Field(None, description="AMR filter (maps to has_amr_info)")
    function: str | None = Field(None, description="Function search (maps to query)")
    cog_category: str | None = Field(
        None, description="COG category (maps to cog_funcats)"
    )

    def model_post_init(self, __context) -> None:
        """Post-initialization to map backward compatibility fields."""
        # Map backward compatibility fields
        if self.species and not self.species_acronym:
            self.species_acronym = self.species
        if self.amr is not None and self.has_amr_info is None:
            self.has_amr_info = self.amr
        if self.function and not self.query:
            self.query = self.function
        if self.cog_category and not self.cog_funcats:
            self.cog_funcats = self.cog_category


class GeneResponseSchema(BaseModel):
    locus_tag: str | None = None
    gene_name: str | None = None
    alias: list[str] | None = None
    product: str | None = None
    start_position: int | None = None
    end_position: int | None = None
    seq_id: str | None = None
    isolate_name: str | None = None
    species_scientific_name: str | None = None
    species_acronym: str | None = None
    uniprot_id: str | None = None
    essentiality: str | None = "Unknown"
    cog_funcats: list[str] | None = None
    cog_id: list[str] | None = None
    kegg: list[str] | None = None
    pfam: list[str] | None = None
    interpro: list[str] | None = None
    ec_number: str | None = None
    dbxref: list[DBXRefSchema] | None = None
    eggnog: str | None = None
    amr: list[AMRSchema] | None = None
    has_amr_info: bool | None = None
    model_config = ConfigDict(from_attributes=True)


class GeneProteinSeqSchema(BaseModel):
    locus_tag: str | None = None
    protein_sequence: str | None = None

    model_config = ConfigDict(from_attributes=True)


class GenePaginationSchema(BasePaginationSchema):
    results: list[GeneResponseSchema]


class EssentialityByContigSchema(BaseModel):
    locus_tag: str
    start: int | None
    end: int | None
    essentiality: str


__all__ = [
    "GeneAutocompleteResponseSchema",
    "GenePaginationSchema",
    "GeneResponseSchema",
    "NaturalLanguageGeneQuery",
]
