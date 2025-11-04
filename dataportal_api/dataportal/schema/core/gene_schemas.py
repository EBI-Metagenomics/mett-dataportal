from typing import Optional, List, Dict, Any

from pydantic import BaseModel, ConfigDict
from pydantic import Field

from dataportal.schema.base_schemas import BasePaginationSchema
from dataportal.utils.constants import (
    DEFAULT_PAGE_SIZE,
    DEFAULT_SORT_DIRECTION,
    DEFAULT_FACET_LIMIT,
)


class GeneAutocompleteQuerySchema(BaseModel):
    """Schema for gene autocomplete endpoint query parameters."""

    query: str = Field(
        ...,
        description="Free-text input to search gene names, locus tags, or annotations.",
    )
    filter: Optional[str] = Field(
        None,
        description="Optional semicolon-separated gene filters, e.g., 'essentiality:essential_liquid;interpro:IPR035952'.",
    )
    limit: int = Field(
        DEFAULT_PAGE_SIZE,
        description="Maximum number of gene suggestions to return.",
    )
    species_acronym: Optional[str] = Field(
        None, description="Optional species acronym filter (e.g., 'BU', 'PV')."
    )
    isolates: Optional[str] = Field(
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
        DEFAULT_PAGE_SIZE, description="Number of genes to return per page."
    )
    sort_field: Optional[str] = Field(
        None,
        description="Field to sort results by (e.g., 'gene_name', 'isolate_name').",
    )
    sort_order: Optional[str] = Field(
        DEFAULT_SORT_DIRECTION, description="Sort order: 'asc' or 'desc'."
    )


class GeneFacetedSearchQuerySchema(BaseModel):
    """Schema for faceted gene search filtering by functional/metadata facets."""

    query: Optional[str] = Field(
        None,
        description="Free-text search across gene fields such as gene name and product.",
    )
    species_acronym: Optional[str] = Field(
        None, description="Species acronym filter (e.g., 'BU', 'PV')."
    )
    essentiality: Optional[str] = Field(
        None, description="Filter by essentiality status, e.g., 'essential'."
    )
    isolates: Optional[str] = Field(
        "", description="Comma-separated list of isolate names to filter."
    )
    cog_id: Optional[str] = Field(
        None, description="Comma-separated list of COG IDs to filter."
    )
    cog_funcats: Optional[str] = Field(
        None, description="Comma-separated list of COG functional categories to filter."
    )
    kegg: Optional[str] = Field(None, description="KEGG pathway or gene ID to filter.")
    go_term: Optional[str] = Field(None, description="GO term ID or label to filter.")
    pfam: Optional[str] = Field(None, description="Pfam domain ID to filter.")
    interpro: Optional[str] = Field(None, description="InterPro ID to filter.")
    has_amr_info: Optional[bool] = Field(
        None, description="Filter genes that have associated AMR information."
    )
    has_essentiality: Optional[bool] = Field(
        None, description="Filter genes that have essentiality data."
    )
    pfam_operator: Optional[str] = Field(
        "OR", description="Logical operator ('AND'/'OR') for Pfam filtering."
    )
    interpro_operator: Optional[str] = Field(
        "OR", description="Logical operator ('AND'/'OR') for InterPro filtering."
    )
    cog_id_operator: Optional[str] = Field(
        "OR", description="Logical operator ('AND'/'OR') for COG ID filtering."
    )
    cog_funcats_operator: Optional[str] = Field(
        "OR",
        description="Logical operator ('AND'/'OR') for COG functional categories filtering.",
    )
    kegg_operator: Optional[str] = Field(
        "OR", description="Logical operator ('AND'/'OR') for KEGG filtering."
    )
    go_term_operator: Optional[str] = Field(
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
    species_acronym: Optional[str] = Field(
        None, description="Species acronym to filter (e.g., 'BU', 'PV')."
    )
    locus_tag: Optional[str] = Field(
        None,
        description="Exact locus tag to search for (takes precedence over query if provided).",
    )
    query: str = Field(
        "",
        description="Free-text search string for gene names, locus tags, or annotations.",
    )
    filter: Optional[str] = Field(
        None,
        description="Additional gene filter, e.g., 'pfam:PF07715;interpro:IPR012910'.",
    )
    filter_operators: Optional[str] = Field(
        None, description="Logical operators for filters, e.g., 'pfam:AND;interpro:OR'."
    )
    page: int = Field(1, description="Page number for pagination (1-based).")
    per_page: int = Field(
        DEFAULT_PAGE_SIZE, description="Number of genes to return per page."
    )
    sort_field: Optional[str] = Field(
        None, description="Field to sort results by, e.g., 'gene_name', 'isolate_name'."
    )
    sort_order: Optional[str] = Field(
        DEFAULT_SORT_DIRECTION, description="Sort order: 'asc' or 'desc'."
    )


class GeneDownloadTSVQuerySchema(BaseModel):
    """Schema for downloading genes as TSV with filtering and sorting."""

    isolates: str = Field(
        "", description="Comma-separated list of isolate names to filter."
    )
    species_acronym: Optional[str] = Field(
        None, description="Species acronym filter (e.g., 'BU', 'PV')."
    )
    query: str = Field(
        "",
        description="Free-text search string for gene names, locus tags, or annotations.",
    )
    filter: Optional[str] = Field(
        None,
        description="Additional gene filter, e.g., 'pfam:PF07715;interpro:IPR012910'.",
    )
    filter_operators: Optional[str] = Field(
        None, description="Logical operators for filters, e.g., 'pfam:AND;interpro:OR'."
    )
    sort_field: Optional[str] = Field(None, description="Field to sort results by.")
    sort_order: Optional[str] = Field(
        DEFAULT_SORT_DIRECTION, description="Sort order: 'asc' or 'desc'."
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
    cog_id: Optional[List[str]] = None
    interpro: Optional[List[str]] = None
    essentiality: Optional[str] = "Unknown"
    feature_type: Optional[str] = "gene"
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
    has_essentiality: bool | None = Field(
        None, description="Filter genes that have essentiality data"
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
    locus_tag: Optional[str] = None
    gene_name: Optional[str] = None
    alias: Optional[List[str]] = None
    product: Optional[str] = None
    product_source: Optional[str] = None 
    start_position: Optional[int] = None
    end_position: Optional[int] = None
    seq_id: Optional[str] = None
    isolate_name: Optional[str] = None
    species_scientific_name: Optional[str] = None
    species_acronym: Optional[str] = None
    uniprot_id: Optional[str] = None
    essentiality: Optional[str] = "Unknown"
    cog_funcats: Optional[List[str]] = None
    cog_id: Optional[List[str]] = None
    kegg: Optional[List[str]] = None
    pfam: Optional[List[str]] = None
    interpro: Optional[List[str]] = None
    ec_number: Optional[str] = None
    dbxref: Optional[List[DBXRefSchema]] = None
    eggnog: Optional[str] = None
    inference: Optional[str] = None
    ontology_terms: Optional[List[Dict[str, Any]]] = None 
    uf_ontology_terms: Optional[List[str]] = None  
    uf_prot_rec_fullname: Optional[str] = None  
    uf_keyword: Optional[List[str]] = None  
    uf_gene_name: Optional[str] = None  
    amr: Optional[List[AMRSchema]] = None
    has_amr_info: Optional[bool] = None
    has_proteomics: Optional[bool] = None
    has_fitness: Optional[bool] = None
    has_mutant_growth: Optional[bool] = None
    has_reactions: Optional[bool] = None
    feature_type: Optional[str] = "gene"
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
    essentiality: Optional[str]


__all__ = [
    "GeneAutocompleteResponseSchema",
    "GenePaginationSchema",
    "GeneResponseSchema",
    "EssentialityByContigSchema",
    "NaturalLanguageGeneQuery",
]
