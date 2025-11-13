import {FacetedFilters, FacetOperators} from '../../stores/filterStore';

/**
 * Normalize a filter value for consistent comparison and storage.
 * Rules:
 * - Boolean values: returned as-is
 * - String values: trimmed of whitespace (preserves original case)
 * 
 * Note: Case-insensitive comparison is handled in compareFilterValues() to match
 * Elasticsearch's lowercase_normalizer for pfam, interpro, kegg, while preserving
 * the original case in the UI.
 * 
 * @param value - The filter value to normalize
 * @returns The normalized value (preserving case)
 */
export const normalizeFilterValue = (value: string | boolean): string | boolean => {
    if (typeof value === 'boolean') {
        return value;
    }
    return String(value).trim(); // Trim whitespace only, preserve case
};

/**
 * Compare two filter values for equality using normalized comparison.
 * 
 * Rules:
 * - Boolean values: compared directly
 * - String values: trimmed and compared case-insensitively
 *   (to match Elasticsearch lowercase_normalizer for pfam, interpro, kegg)
 * 
 * Note: This enables case-insensitive matching while preserving original case in the UI.
 * 
 * @param a - First value to compare
 * @param b - Second value to compare
 * @returns True if values are equal after normalization (case-insensitive for strings)
 */
export const compareFilterValues = (a: string | boolean, b: string | boolean): boolean => {
    // Handle boolean values
    if (typeof a === 'boolean' && typeof b === 'boolean') {
        return a === b;
    }
    if (typeof a === 'boolean' || typeof b === 'boolean') {
        return false; // Different types
    }
    
    // For strings: trim and compare case-insensitively
    // We know they're strings at this point after the boolean checks above
    const normalizedA = normalizeFilterValue(a);
    const normalizedB = normalizeFilterValue(b);
    if (typeof normalizedA === 'string' && typeof normalizedB === 'string') {
        return normalizedA.toLowerCase() === normalizedB.toLowerCase();
    }
    return normalizedA === normalizedB;
};

/**
 * Normalize an array of filter values, removing duplicates.
 * 
 * @param values - Array of filter values to normalize
 * @returns Array of unique normalized values
 */
export const normalizeFilterValues = (values: (string | boolean)[]): (string | boolean)[] => {
    const normalized = values.map(v => normalizeFilterValue(v));
    // Use Map to preserve order while removing duplicates
    const seen = new Map<string | boolean, boolean>();
    const unique: (string | boolean)[] = [];
    
    for (const val of normalized) {
        if (!seen.has(val)) {
            seen.set(val, true);
            unique.push(val);
        }
    }
    
    return unique;
};

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
        // For KEGG: add 'ko:' prefix back for API queries (Elasticsearch stores with prefix)
        // Frontend stores without prefix (removed in FeaturePanel), but API needs with prefix
        result.kegg = filters.kegg.map(v => {
            const value = String(v);
            // If value doesn't already start with 'ko:', add it
            if (!value.toLowerCase().startsWith('ko:')) {
                return `ko:${value}`;
            }
            return value;
        });
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