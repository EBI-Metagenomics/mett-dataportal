// Application constants
export const APP_CONSTANTS = {
  // Loading and timing
  MIN_LOADING_TIME: 500, // milliseconds
  SPINNER_DELAY: 500, // milliseconds
  
  // Default values
  DEFAULT_SORT_FIELD: 'species',
  DEFAULT_SORT_ORDER: 'asc' as const,
  DEFAULT_GENE_SORT_FIELD: 'locus_tag',
  
  // URL parameters
  URL_PARAMS: {
    SPECIES: 'species',
    TYPE_STRAINS: 'typeStrains',
    SEARCH: 'search',
    SORT_FIELD: 'sortField',
    SORT_ORDER: 'sortOrder',
  },
  
  // Tab IDs
  TABS: {
    GENOME_SEARCH: 'vf-tabs__section--1',
    GENE_SEARCH: 'vf-tabs__section--2',
    PYHMMER_SEARCH: 'vf-tabs__section--3',
  },
  
  // Link templates
  LINK_TEMPLATES: {
    GENOME: '/genome/${strain_name}',
    GENE: '/genome/${strain_name}?locus_tag=${locus_tag}',
  },
  
  // Error messages
  ERROR_MESSAGES: {
    FETCH_SPECIES: 'Failed to load species and type strain data',
    FETCH_GENOMES: 'Failed to load genome data',
    UPDATE_SPECIES: 'Failed to update species selection',
    UPDATE_TYPE_STRAINS: 'Failed to update type strain selection',
    SEARCH_GENOMES: 'Failed to search genomes',
    SEARCH_GENES: 'Failed to search genes',
    SORT_GENOMES: 'Failed to sort genomes',
    SORT_GENES: 'Failed to sort genes',
  },
} as const;

// Type definitions for constants
export type SortOrder = typeof APP_CONSTANTS.DEFAULT_SORT_ORDER;
export type TabId = typeof APP_CONSTANTS.TABS[keyof typeof APP_CONSTANTS.TABS]; 

// Pyhmmer help text for popovers
export const PYHMMER_CUTOFF_HELP = `
E-value: Expected number of false positives. Lower values are more stringent (e.g., 0.01 means 1% chance of false positive).

Bit Score: Log-odds score for alignment quality. Higher values indicate better alignments.

Significance: Threshold for including hits in results.

Report: Threshold for reporting hits in output.
`;

export const PYHMMER_GAP_PENALTIES_HELP = `
Gap open and extension penalties control the cost of introducing and extending gaps in the alignment. Lower values allow more gaps; higher values penalize gaps more strongly. Default values are usually appropriate for most searches.
`;

export const PYHMMER_FILTER_HELP = `
The bias composition filter reduces the impact of low-complexity or biased regions in protein sequences, which can otherwise lead to spurious hits. It is recommended to keep this filter enabled unless you have a specific reason to turn it off.
`; 