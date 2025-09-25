/**
 * Isolate name extraction utilities for PyHMMER search
 * Extracts isolate name from locus_tag for database selection
 */

/**
 * Extract isolate name from locus_tag
 * Format: BU_ATCC8492_00001 -> BU_ATCC8492
 * Format: PV_ATCC8482_00001 -> PV_ATCC8482
 */
export function extractIsolateFromLocusTag(locusTag: string): string | null {
    if (!locusTag) return null;
    
    // Match pattern: [SPECIES]_[ISOLATE]_[NUMBER]
    // Extract everything up to the last underscore
    const lastUnderscoreIndex = locusTag.lastIndexOf('_');
    if (lastUnderscoreIndex === -1) return null;
    
    const isolate = locusTag.substring(0, lastUnderscoreIndex);
    console.log('IsolateExtraction: Extracted isolate from locus_tag:', locusTag, '->', isolate);
    return isolate;
}

/**
 * Determine species from locus_tag
 * BU_* -> 'BU'
 * PV_* -> 'PV'
 */
export function getSpeciesFromLocusTag(locusTag: string): 'BU' | 'PV' | null {
    if (!locusTag) return null;
    
    const species = locusTag.substring(0, 2).toUpperCase();
    if (species === 'BU' || species === 'PV') {
        return species;
    }
    
    return null;
}

/**
 * Get isolate and species information from locus_tag
 * Returns both the isolate name and species for database selection
 */
export function getIsolateInfo(locusTag: string): {
    isolate: string | null;
    species: 'BU' | 'PV' | null;
} {
    const isolate = extractIsolateFromLocusTag(locusTag);
    const species = getSpeciesFromLocusTag(locusTag);
    
    return {
        isolate,
        species
    };
}
