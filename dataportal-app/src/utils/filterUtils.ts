import { FacetedFilters, FacetOperators } from '../stores/filterStore';

/**
 * Convert FacetedFilters to the legacy Record<string, string[]> format
 * used by the API for backward compatibility
 */
export const convertFacetedFiltersToLegacy = (filters: FacetedFilters): Record<string, string[]> => {
  const result: Record<string, string[]> = {};
  
  if (filters.essentiality) {
    result.essentiality = filters.essentiality;
  }
  if (filters.has_amr_info) {
    result.has_amr_info = filters.has_amr_info.map(v => String(v));
  }
  if (filters.pfam) {
    result.pfam = filters.pfam;
  }
  if (filters.interpro) {
    result.interpro = filters.interpro;
  }
  if (filters.kegg) {
    result.kegg = filters.kegg;
  }
  if (filters.cog_funcats) {
    result.cog_funcats = filters.cog_funcats;
  }
  if (filters.cog_id) {
    result.cog_id = filters.cog_id;
  }
  if (filters.go_term) {
    result.go_term = filters.go_term;
  }
  
  return result;
};

/**
 * Convert FacetOperators to Record<string, 'AND' | 'OR'> format
 */
export const convertFacetOperatorsToLegacy = (operators: FacetOperators): Record<string, 'AND' | 'OR'> => {
  const result: Record<string, 'AND' | 'OR'> = {};
  
  if (operators.pfam) {
    result.pfam = operators.pfam;
  }
  if (operators.interpro) {
    result.interpro = operators.interpro;
  }
  if (operators.cog_id) {
    result.cog_id = operators.cog_id;
  }
  if (operators.cog_funcats) {
    result.cog_funcats = operators.cog_funcats;
  }
  if (operators.kegg) {
    result.kegg = operators.kegg;
  }
  if (operators.go_term) {
    result.go_term = operators.go_term;
  }
  
  return result;
};

/**
 * Convert legacy Record<string, string[]> format to FacetedFilters
 */
export const convertLegacyToFacetedFilters = (legacy: Record<string, string[]>): FacetedFilters => {
  const result: FacetedFilters = {};
  
  if (legacy.essentiality) {
    result.essentiality = legacy.essentiality;
  }
  if (legacy.has_amr_info) {
    result.has_amr_info = legacy.has_amr_info.map(v => v === 'true');
  }
  if (legacy.pfam) {
    result.pfam = legacy.pfam;
  }
  if (legacy.interpro) {
    result.interpro = legacy.interpro;
  }
  if (legacy.kegg) {
    result.kegg = legacy.kegg;
  }
  if (legacy.cog_funcats) {
    result.cog_funcats = legacy.cog_funcats;
  }
  if (legacy.cog_id) {
    result.cog_id = legacy.cog_id;
  }
  if (legacy.go_term) {
    result.go_term = legacy.go_term;
  }
  
  return result;
}; 