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