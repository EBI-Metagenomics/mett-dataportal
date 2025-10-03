"""
Schemas for Pooled TTP (Thermal Proteome Profiling) API endpoints.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from dataportal.schema.base_schemas import BasePaginationSchema
from dataportal.utils.constants import DEFAULT_PER_PAGE_CNT, DEFAULT_SORT


# ===== REQUEST SCHEMAS =====

class TTPInteractionQuerySchema(BaseModel):
    """Schema for basic TTP interaction search."""
    
    query: str = Field(
        "",
        description="Free-text search term to match against gene names, locus tags, or compound names."
    )
    page: int = Field(1, description="Page number for pagination (1-based).")
    per_page: int = Field(
        DEFAULT_PER_PAGE_CNT, 
        description="Number of interactions to return per page."
    )
    sort_field: Optional[str] = Field(
        None,
        description="Field to sort results by (e.g., 'ttp_score', 'fdr', 'compound')."
    )
    sort_order: Optional[str] = Field(
        DEFAULT_SORT, 
        description="Sort order: 'asc' or 'desc'."
    )


class TTPFacetedSearchQuerySchema(BaseModel):
    """Schema for faceted TTP search with advanced filtering."""
    
    query: Optional[str] = Field(
        None,
        description="Free-text search across gene names, locus tags, and compound names."
    )
    locus_tag: Optional[str] = Field(
        None,
        description="Exact locus tag to search for."
    )
    compound: Optional[str] = Field(
        None,
        description="Compound name to filter by."
    )
    species_acronym: Optional[str] = Field(
        None, 
        description="Species acronym filter (e.g., 'BU', 'PV')."
    )
    isolate_name: Optional[str] = Field(
        None,
        description="Isolate name to filter by."
    )
    hit_calling: Optional[bool] = Field(
        None,
        description="Filter by hit calling status (true for significant interactions)."
    )
    poolA: Optional[str] = Field(
        None,
        description="Filter by poolA (e.g., 'pool1', 'pool2')."
    )
    poolB: Optional[str] = Field(
        None,
        description="Filter by poolB (e.g., 'pool8', 'pool9')."
    )
    assay: Optional[str] = Field(
        None,
        description="Filter by assay type (e.g., 'pooled_TPP_lysate')."
    )
    min_ttp_score: Optional[float] = Field(
        None,
        description="Minimum TTP score threshold."
    )
    max_ttp_score: Optional[float] = Field(
        None,
        description="Maximum TTP score threshold."
    )
    min_fdr: Optional[float] = Field(
        None,
        description="Minimum FDR threshold."
    )
    max_fdr: Optional[float] = Field(
        None,
        description="Maximum FDR threshold."
    )
    page: int = Field(1, description="Page number for pagination (1-based).")
    per_page: int = Field(
        DEFAULT_PER_PAGE_CNT,
        description="Number of interactions to return per page."
    )
    sort_field: Optional[str] = Field(
        None,
        description="Field to sort results by."
    )
    sort_order: Optional[str] = Field(
        DEFAULT_SORT,
        description="Sort order: 'asc' or 'desc'."
    )


class TTPGeneInteractionsQuerySchema(BaseModel):
    """Schema for getting all interactions for a specific gene."""
    
    locus_tag: Optional[str] = Field(
        None,
        description="Locus tag of the gene to get interactions for (provided as path parameter)."
    )
    hit_calling: Optional[bool] = Field(
        None,
        description="Filter by hit calling status."
    )
    poolA: Optional[str] = Field(
        None,
        description="Filter by poolA."
    )
    poolB: Optional[str] = Field(
        None,
        description="Filter by poolB."
    )
    min_ttp_score: Optional[float] = Field(
        None,
        description="Minimum TTP score threshold."
    )
    sort_field: Optional[str] = Field(
        "ttp_score",
        description="Field to sort results by."
    )
    sort_order: Optional[str] = Field(
        "desc",
        description="Sort order: 'asc' or 'desc'."
    )


class TTPCompoundInteractionsQuerySchema(BaseModel):
    """Schema for getting all interactions for a specific compound."""
    
    compound: Optional[str] = Field(
        None,
        description="Name of the compound to get interactions for (provided as path parameter)."
    )
    hit_calling: Optional[bool] = Field(
        None,
        description="Filter by hit calling status."
    )
    species_acronym: Optional[str] = Field(
        None,
        description="Species acronym filter."
    )
    isolate_name: Optional[str] = Field(
        None,
        description="Isolate name filter."
    )
    min_ttp_score: Optional[float] = Field(
        None,
        description="Minimum TTP score threshold."
    )
    sort_field: Optional[str] = Field(
        "ttp_score",
        description="Field to sort results by."
    )
    sort_order: Optional[str] = Field(
        "desc",
        description="Sort order: 'asc' or 'desc'."
    )


class TTPHitAnalysisQuerySchema(BaseModel):
    """Schema for hit analysis - finding significant interactions."""
    
    min_ttp_score: Optional[float] = Field(
        None,
        description="Minimum TTP score threshold for hits."
    )
    max_fdr: Optional[float] = Field(
        0.05,
        description="Maximum FDR threshold for hits."
    )
    compound: Optional[str] = Field(
        None,
        description="Filter by specific compound."
    )
    species_acronym: Optional[str] = Field(
        None,
        description="Species acronym filter."
    )
    poolA: Optional[str] = Field(
        None,
        description="Filter by poolA."
    )
    poolB: Optional[str] = Field(
        None,
        description="Filter by poolB."
    )
    page: int = Field(1, description="Page number for pagination.")
    per_page: int = Field(
        DEFAULT_PER_PAGE_CNT,
        description="Number of hits to return per page."
    )


class TTPPoolAnalysisQuerySchema(BaseModel):
    """Schema for pool-based analysis."""
    
    poolA: Optional[str] = Field(
        None,
        description="Filter by poolA."
    )
    poolB: Optional[str] = Field(
        None,
        description="Filter by poolB."
    )
    species_acronym: Optional[str] = Field(
        None,
        description="Species acronym filter."
    )
    hit_calling: Optional[bool] = Field(
        None,
        description="Filter by hit calling status."
    )
    min_ttp_score: Optional[float] = Field(
        None,
        description="Minimum TTP score threshold."
    )


class TTPDownloadQuerySchema(BaseModel):
    """Schema for downloading TTP data."""
    
    query: Optional[str] = Field(
        None,
        description="Free-text search term."
    )
    locus_tag: Optional[str] = Field(
        None,
        description="Locus tag filter."
    )
    compound: Optional[str] = Field(
        None,
        description="Compound filter."
    )
    hit_calling: Optional[bool] = Field(
        None,
        description="Hit calling filter."
    )
    poolA: Optional[str] = Field(
        None,
        description="PoolA filter."
    )
    poolB: Optional[str] = Field(
        None,
        description="PoolB filter."
    )
    min_ttp_score: Optional[float] = Field(
        None,
        description="Minimum TTP score threshold."
    )
    max_fdr: Optional[float] = Field(
        None,
        description="Maximum FDR threshold."
    )
    format: str = Field(
        "csv",
        description="Download format: 'csv' or 'tsv'."
    )


# ===== RESPONSE SCHEMAS =====

class TTPCompoundInteractionSchema(BaseModel):
    """Schema for individual compound interaction within a gene."""
    
    compound: str = Field(..., description="Compound name")
    ttp_score: Optional[float] = Field(None, description="TTP score")
    fdr: Optional[float] = Field(None, description="False discovery rate")
    hit_calling: bool = Field(..., description="Hit calling status")
    notes: Optional[str] = Field(None, description="Additional notes")
    assay: Optional[str] = Field(None, description="Assay type")
    poolA: Optional[str] = Field(None, description="Pool A")
    poolB: Optional[str] = Field(None, description="Pool B")
    experimental_condition: Optional[str] = Field(None, description="Experimental condition")


class TTPGeneInteractionSchema(BaseModel):
    """Schema for gene with its compound interactions grouped together."""
    
    locus_tag: str = Field(..., description="Gene locus tag")
    gene_name: Optional[str] = Field(None, description="Gene name")
    product: Optional[str] = Field(None, description="Gene product")
    uniprot_id: Optional[str] = Field(None, description="UniProt ID")
    species_acronym: Optional[str] = Field(None, description="Species acronym")
    isolate_name: Optional[str] = Field(None, description="Isolate name")
    compounds: List[TTPCompoundInteractionSchema] = Field(..., description="List of compound interactions for this gene")


# Keep the old schema for backward compatibility if needed
class TTPInteractionSchema(BaseModel):
    """Schema for individual TTP interaction (legacy - use TTPGeneInteractionSchema instead)."""
    
    locus_tag: str = Field(..., description="Gene locus tag")
    gene_name: Optional[str] = Field(None, description="Gene name")
    product: Optional[str] = Field(None, description="Gene product")
    uniprot_id: Optional[str] = Field(None, description="UniProt ID")
    species_acronym: Optional[str] = Field(None, description="Species acronym")
    isolate_name: Optional[str] = Field(None, description="Isolate name")
    compound: str = Field(..., description="Compound name")
    ttp_score: Optional[float] = Field(None, description="TTP score")
    fdr: Optional[float] = Field(None, description="False discovery rate")
    hit_calling: bool = Field(..., description="Hit calling status")
    notes: Optional[str] = Field(None, description="Additional notes")
    assay: Optional[str] = Field(None, description="Assay type")
    poolA: Optional[str] = Field(None, description="Pool A")
    poolB: Optional[str] = Field(None, description="Pool B")
    experimental_condition: Optional[str] = Field(None, description="Experimental condition")


class TTPInteractionResponseSchema(BasePaginationSchema):
    """Schema for paginated TTP interaction response with grouped interactions."""
    
    results: List[TTPGeneInteractionSchema] = Field(..., description="List of genes with their compound interactions")


class TTPHitSummarySchema(BaseModel):
    """Schema for hit analysis summary."""
    
    total_interactions: int = Field(..., description="Total number of interactions")
    total_hits: int = Field(..., description="Number of significant hits")
    hit_rate: float = Field(..., description="Hit rate (hits/total)")
    avg_ttp_score: Optional[float] = Field(None, description="Average TTP score")
    median_ttp_score: Optional[float] = Field(None, description="Median TTP score")
    min_ttp_score: Optional[float] = Field(None, description="Minimum TTP score")
    max_ttp_score: Optional[float] = Field(None, description="Maximum TTP score")


class TTPPoolSummarySchema(BaseModel):
    """Schema for pool analysis summary."""
    
    poolA: Optional[str] = Field(None, description="Pool A identifier")
    poolB: Optional[str] = Field(None, description="Pool B identifier")
    total_interactions: int = Field(..., description="Total interactions in pool")
    total_hits: int = Field(..., description="Number of hits in pool")
    hit_rate: float = Field(..., description="Hit rate in pool")
    compounds: List[str] = Field(..., description="List of compounds in pool")
    top_compounds: List[Dict[str, Any]] = Field(..., description="Top compounds by hit count")


class TTPCompoundSummarySchema(BaseModel):
    """Schema for compound summary information."""
    
    compound: str = Field(..., description="Compound name")
    total_interactions: int = Field(..., description="Total interactions")
    total_hits: int = Field(..., description="Number of hits")
    hit_rate: float = Field(..., description="Hit rate")
    avg_ttp_score: Optional[float] = Field(None, description="Average TTP score")
    poolA: Optional[str] = Field(None, description="Pool A")
    poolB: Optional[str] = Field(None, description="Pool B")


class TTPGeneSummarySchema(BaseModel):
    """Schema for gene summary information."""
    
    locus_tag: str = Field(..., description="Gene locus tag")
    gene_name: Optional[str] = Field(None, description="Gene name")
    product: Optional[str] = Field(None, description="Gene product")
    species_acronym: Optional[str] = Field(None, description="Species acronym")
    total_interactions: int = Field(..., description="Total interactions")
    total_hits: int = Field(..., description="Number of hits")
    hit_rate: float = Field(..., description="Hit rate")
    avg_ttp_score: Optional[float] = Field(None, description="Average TTP score")


class TTPMetadataSchema(BaseModel):
    """Schema for TTP metadata information."""
    
    total_interactions: int = Field(..., description="Total number of interactions")
    total_genes: int = Field(..., description="Total number of genes")
    total_compounds: int = Field(..., description="Total number of compounds")
    total_hits: int = Field(..., description="Total number of hits")
    hit_rate: float = Field(..., description="Overall hit rate")
    available_pools: List[str] = Field(..., description="Available experimental pools")
    available_compounds: List[str] = Field(..., description="Available compounds")
    score_range: Dict[str, float] = Field(..., description="TTP score range (min, max, avg)")


class TTPAutocompleteSchema(BaseModel):
    """Schema for autocomplete suggestions."""
    
    suggestions: List[str] = Field(..., description="List of suggestions")
    total: int = Field(..., description="Total number of suggestions")


# ===== FACET SCHEMAS =====

class TTPFacetSchema(BaseModel):
    """Schema for faceted search facets."""
    
    compounds: List[Dict[str, Any]] = Field(..., description="Compound facets")
    pools: List[Dict[str, Any]] = Field(..., description="Pool facets")
    species: List[Dict[str, Any]] = Field(..., description="Species facets")
    isolates: List[Dict[str, Any]] = Field(..., description="Isolate facets")
    hit_calling: List[Dict[str, Any]] = Field(..., description="Hit calling facets")
    assays: List[Dict[str, Any]] = Field(..., description="Assay facets")
    score_ranges: Dict[str, float] = Field(..., description="Score range facets")
