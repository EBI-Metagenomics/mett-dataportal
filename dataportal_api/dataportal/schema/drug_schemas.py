"""
Pydantic schemas for drug MIC and metabolism data endpoints.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from dataportal.schema.base_schemas import BasePaginationSchema


class DrugMICDataSchema(BaseModel):
    """Schema for individual drug MIC measurement."""
    
    model_config = ConfigDict(populate_by_name=True)
    
    drug_name: Optional[str] = Field(None, description="Name of the drug")
    drug_class: Optional[str] = Field(None, description="Drug class (e.g., beta_lactam)")
    drug_subclass: Optional[str] = Field(None, description="Drug subclass")
    compound_name: Optional[str] = Field(None, description="Chemical compound name")
    pubchem_id: Optional[str] = Field(None, description="PubChem compound ID")
    
    relation: Optional[str] = Field(None, description="MIC relation (=, >, <=, etc.)")
    mic_value: Optional[float] = Field(None, description="MIC value")
    unit: Optional[str] = Field(None, description="Unit of measurement (uM, mg/L)")
    
    experimental_condition_id: Optional[int] = Field(None, description="Experimental condition ID")
    experimental_condition_name: Optional[str] = Field(None, description="Experimental condition name")


class DrugMetabolismDataSchema(BaseModel):
    """Schema for individual drug metabolism measurement."""
    
    model_config = ConfigDict(populate_by_name=True)
    
    drug_name: Optional[str] = Field(None, description="Name of the drug")
    drug_class: Optional[str] = Field(None, description="Drug class (e.g., beta_lactam)")
    drug_subclass: Optional[str] = Field(None, description="Drug subclass")
    compound_name: Optional[str] = Field(None, description="Chemical compound name")
    pubchem_id: Optional[str] = Field(None, description="PubChem compound ID")
    
    degr_percent: Optional[float] = Field(None, description="Degradation percentage")
    pval: Optional[float] = Field(None, description="P-value")
    fdr: Optional[float] = Field(None, description="False Discovery Rate")
    metabolizer_classification: Optional[str] = Field(None, description="Metabolizer classification")
    is_significant: Optional[bool] = Field(None, description="Whether the result is statistically significant")
    
    experimental_condition_id: Optional[int] = Field(None, description="Experimental condition ID")
    experimental_condition_name: Optional[str] = Field(None, description="Experimental condition name")


class StrainDrugMICResponseSchema(BaseModel):
    """Response schema for strain drug MIC data."""
    
    isolate_name: str = Field(..., description="Strain isolate name")
    species_acronym: Optional[str] = Field(None, description="Species acronym")
    species_scientific_name: Optional[str] = Field(None, description="Species scientific name")
    drug_mic_data: List[DrugMICDataSchema] = Field(default_factory=list, description="List of drug MIC measurements")


class StrainDrugMetabolismResponseSchema(BaseModel):
    """Response schema for strain drug metabolism data."""
    
    isolate_name: str = Field(..., description="Strain isolate name")
    species_acronym: Optional[str] = Field(None, description="Species acronym")
    species_scientific_name: Optional[str] = Field(None, description="Species scientific name")
    drug_metabolism_data: List[DrugMetabolismDataSchema] = Field(default_factory=list, description="List of drug metabolism measurements")


class StrainDrugDataResponseSchema(BaseModel):
    """Response schema for combined strain drug data (MIC + metabolism)."""
    
    isolate_name: str = Field(..., description="Strain isolate name")
    species_acronym: Optional[str] = Field(None, description="Species acronym")
    species_scientific_name: Optional[str] = Field(None, description="Species scientific name")
    drug_mic_data: List[DrugMICDataSchema] = Field(default_factory=list, description="List of drug MIC measurements")
    drug_metabolism_data: List[DrugMetabolismDataSchema] = Field(default_factory=list, description="List of drug metabolism measurements")


# Drug-centric search schemas
class DrugMICSearchQuerySchema(BaseModel):
    """Query schema for drug MIC search."""
    
    query: str = Field("", description="Search term for drug name, class, or strain")
    drug_name: Optional[str] = Field(None, description="Filter by specific drug name")
    drug_class: Optional[str] = Field(None, description="Filter by drug class")
    species_acronym: Optional[str] = Field(None, description="Filter by species acronym")
    min_mic_value: Optional[float] = Field(None, description="Minimum MIC value threshold")
    max_mic_value: Optional[float] = Field(None, description="Maximum MIC value threshold")
    unit: Optional[str] = Field(None, description="Filter by unit (uM, mg/L)")
    experimental_condition: Optional[str] = Field(None, description="Filter by experimental condition")
    page: int = Field(1, description="Page number")
    per_page: int = Field(20, description="Number of results per page")
    sort_by: Optional[str] = Field("isolate_name", description="Sort field (isolate_name, species_acronym, species_scientific_name). Uses keyword fields for sorting.")
    sort_order: Optional[str] = Field("asc", description="Sort order (asc, desc)")


class DrugMetabolismSearchQuerySchema(BaseModel):
    """Query schema for drug metabolism search."""
    
    query: str = Field("", description="Search term for drug name, class, or strain")
    drug_name: Optional[str] = Field(None, description="Filter by specific drug name")
    drug_class: Optional[str] = Field(None, description="Filter by drug class")
    species_acronym: Optional[str] = Field(None, description="Filter by species acronym")
    min_fdr: Optional[float] = Field(None, description="Maximum FDR threshold (e.g., 0.05)")
    min_degr_percent: Optional[float] = Field(None, description="Minimum degradation percentage")
    metabolizer_classification: Optional[str] = Field(None, description="Filter by metabolizer classification")
    is_significant: Optional[bool] = Field(None, description="Filter by statistical significance")
    experimental_condition: Optional[str] = Field(None, description="Filter by experimental condition")
    page: int = Field(1, description="Page number")
    per_page: int = Field(20, description="Number of results per page")
    sort_by: Optional[str] = Field("isolate_name", description="Sort field (isolate_name, species_acronym, species_scientific_name). Uses keyword fields for sorting.")
    sort_order: Optional[str] = Field("asc", description="Sort order (asc, desc)")


class DrugMICSearchResultSchema(BaseModel):
    """Individual result schema for drug MIC search."""
    
    isolate_name: str = Field(..., description="Strain isolate name")
    species_acronym: Optional[str] = Field(None, description="Species acronym")
    species_scientific_name: Optional[str] = Field(None, description="Species scientific name")
    drug_name: Optional[str] = Field(None, description="Drug name")
    drug_class: Optional[str] = Field(None, description="Drug class")
    mic_value: Optional[float] = Field(None, description="MIC value")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    relation: Optional[str] = Field(None, description="MIC relation")
    experimental_condition_name: Optional[str] = Field(None, description="Experimental condition")


class DrugMetabolismSearchResultSchema(BaseModel):
    """Individual result schema for drug metabolism search."""
    
    isolate_name: str = Field(..., description="Strain isolate name")
    species_acronym: Optional[str] = Field(None, description="Species acronym")
    species_scientific_name: Optional[str] = Field(None, description="Species scientific name")
    drug_name: Optional[str] = Field(None, description="Drug name")
    drug_class: Optional[str] = Field(None, description="Drug class")
    degr_percent: Optional[float] = Field(None, description="Degradation percentage")
    pval: Optional[float] = Field(None, description="P-value")
    fdr: Optional[float] = Field(None, description="False Discovery Rate")
    metabolizer_classification: Optional[str] = Field(None, description="Metabolizer classification")
    is_significant: Optional[bool] = Field(None, description="Statistical significance")
    experimental_condition_name: Optional[str] = Field(None, description="Experimental condition")


# Pagination schemas
class DrugMICPaginationSchema(BasePaginationSchema):
    """Pagination schema for drug MIC search results."""
    results: List[DrugMICSearchResultSchema]


class DrugMetabolismPaginationSchema(BasePaginationSchema):
    """Pagination schema for drug metabolism search results."""
    results: List[DrugMetabolismSearchResultSchema]


# Autocomplete schemas
class DrugSuggestionSchema(BaseModel):
    """Schema for drug name suggestions."""
    drug_name: str = Field(..., description="Drug name")
    drug_class: Optional[str] = Field(None, description="Drug class")
    count: int = Field(..., description="Number of strains with this drug")


class DrugAutocompleteQuerySchema(BaseModel):
    """Query schema for drug autocomplete."""
    query: str = Field(..., description="Search term for drug name autocomplete")
    limit: int = Field(10, description="Maximum number of suggestions to return")
    species_acronym: Optional[str] = Field(None, description="Optional species acronym filter (BU, PV)")
    data_type: str = Field("mic", description="Type of data to search (mic, metabolism)")
