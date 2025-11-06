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

// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
export const API_GENOMES_BY_ISOLATE_NAMES = `${API_BASE_URL}/genomes/by-isolate-names`;
export const API_GENOME_SEARCH = `${API_BASE_URL}/genomes/search`;
export const API_GENE_SEARCH_ADVANCED = `${API_BASE_URL}/genes/search/advanced`;

export const getAPIUrlGenomeSearchWithSpecies = (species_acronym: string) => 
  `${API_BASE_URL}/species/${species_acronym}/genomes/search`;

export const getEssentialityDataUrl = (isolate_name: string) => 
  `${API_BASE_URL}/genomes/${isolate_name}/essentiality`;

// External Database URLs
export const EXTERNAL_DB_URLS = {
  PFAM: import.meta.env.VITE_PFAM_URL || 'https://pfam.xfam.org/family/',
  INTERPRO: import.meta.env.VITE_INTERPRO_URL || 'https://www.ebi.ac.uk/interpro/protein/entry/',
  KEGG: import.meta.env.VITE_KEGG_URL || 'https://www.kegg.jp/kegg-bin/show_pathway?',
  COG: import.meta.env.VITE_COG_URL || 'https://www.ncbi.nlm.nih.gov/research/cog/protein/',
  COG_CATEGORY: import.meta.env.VITE_COG_CATEGORY_URL || 'https://www.ncbi.nlm.nih.gov/research/cog/cogcategory/',
  GO: import.meta.env.VITE_GO_URL || 'https://quickgo.org/term/',
  UNIPROT: import.meta.env.VITE_BACINTERACTOME_SHINY_APP_URL || 'https://www.uniprot.org/uniprot/',
} as const;

// Bacinteractome Configuration
export const BACINTERACTOME_SHINY_APP_BASE_URL = import.meta.env.VITE_BACINTERACTOME_SHINY_APP_URL;

// EBI and External Links
export const EBI_FTP_SERVER = "https://ftp.ebi.ac.uk/pub/databases/mett/";
export const EXT_LINK_ESSENTIALITY_JOURNAL = "https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1004401";
export const EXT_LINK_AMR_DETERMINATION = "https://github.com/ncbi/amr";

// Essentiality and AMR Text
export const ESSENTIALITY_DETERMINATION_TXT = "Gene essentiality was determined by analyzing transposon insertion\n" +
  "                                                    libraries using the software package TRANSIT (DeJesus et al. 2015).\n" +
  "                                                    Libraries were created using a Mariner transposon and by outgrowth\n" +
  "                                                    of mutants in either liquid or solid mGAM (rich undefined) culture\n" +
  "                                                    media.";

export const AMR_DETERMINATION_TXT = "Antimicrobial resistance (AMR) information was determined using AMRFinderPlus.";

// UI Configuration
export const SPINNER_DELAY = 200;
export const DEFAULT_PER_PAGE_CNT = 10;
export const FACET_INITIAL_VISIBLE_CNT = 10;
export const FACET_STEP_CNT = 10;
export const TABLE_MAX_COLUMNS = 15;

// Gene Table Configuration
export const GENE_TABLE_CONFIG = {
  SHOW_ANNOTATION_INDICATORS: true, // Toggle to show/hide annotation availability column
} as const;

// Annotation availability indicators with color coding - using bordered boxes
export const ANNOTATION_INDICATORS = {
  interpro: { icon: 'I', label: 'InterPro', color: '#2a7aaf' },      // Blue
  pfam: { icon: 'P', label: 'PFAM', color: '#1c8748' },              // Green
  kegg: { icon: 'K', label: 'KEGG', color: '#c57e0c' },              // Orange
  cog_id: { icon: 'C', label: 'COG', color: '#9b59b6' },             // Purple
  ontology_terms: { icon: 'G', label: 'GO Terms', color: '#e67e22' }, // Dark Orange
  amr: { icon: 'A', label: 'AMR', color: '#a8362a' },                // Red
} as const;

// Example sequence constant
export const EXAMPLE_SEQUENCE = `>Example protein sequence\nMSEIDHVGLWNRCLEIIRDNVPEQTYKTWFLPIIPLKYEDKTLV`;

// Facet Configuration
export const FACET_ORDER = [
  'essentiality',
  'has_amr_info',
  'pfam',
  'interpro',
  'kegg',
  'cog_funcats',
  'cog_id',
];

export const LOGICAL_OPERATOR_FACETS = [
  'pfam',
  'interpro',
  'cog_id',
  'cog_funcats',
  'go_term',
  'kegg'
];

// Display Settings
export const DISPLAY_SETTINGS = {
  DEFAULT_BUFFER: 10000,
};

// Zoom Configuration
export const ZOOM_LEVELS = {
  MIN: -2,
  MAX: 5,
  NAV: 10,  // Navigation zoom level
  BP_PER_PX: 10,  // Base pairs per pixel for track display
} as const;

// JBrowse Track Height Configuration
export const JBROWSE_TRACK_HEIGHTS = {
  // Reference sequence track (assembly/DNA sequence)
  REFERENCE_SEQUENCE: 40,
  REFERENCE_SEQUENCE_MIN: 30,
  REFERENCE_SEQUENCE_MAX: 50,
  
  // Structural annotation track (genes)
  STRUCTURAL_ANNOTATION: 250,
  STRUCTURAL_ANNOTATION_MIN: 250,
  STRUCTURAL_ANNOTATION_MAX: 400,
  
  // Individual gene feature height
  GENE_FEATURE_HEIGHT: 15,
  
  // Default track rendering container
  DEFAULT_MIN_HEIGHT: 200,
} as const;
