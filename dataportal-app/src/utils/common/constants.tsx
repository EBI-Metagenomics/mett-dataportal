import React from 'react';

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

// PyHMMER help text for popovers
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
  UNIPROT: import.meta.env.VITE_UNIPROT_URL || 'https://www.uniprot.org/uniprot/',
} as const;

// External Database Link Generation
export const generateExternalDbLink = (dbType: keyof typeof EXTERNAL_DB_URLS, id: string): string => {
  const baseUrl = EXTERNAL_DB_URLS[dbType];

  switch (dbType) {
    case 'PFAM': {
      return `${baseUrl}${id}`;
    }
    case 'INTERPRO': {
      return `${baseUrl}${id}`;
    }
    case 'KEGG': {
      const keggId = id.startsWith('ko:') ? id.substring(3) : id;
      return `${baseUrl}${keggId}`;
    }
    case 'COG': {
      return `${baseUrl}${id}`;
    }
    case 'COG_CATEGORY': {
      return `${baseUrl}${id}`;
    }
    case 'UNIPROT': {
      return `${baseUrl}${id}`;
    }
    case 'GO': {
      return `${baseUrl}${id}`;
    }
    default:
      return `${baseUrl}${id}`;
  }
};

// Bacinteractome Configuration
export const BACINTERACTOME_SHINY_APP_BASE_URL = import.meta.env.VITE_BACINTERACTOME_SHINY_APP_URL;
export const getBacinteractomeUniprotUrl = (uniprot_id: string, species_name: string) => 
  `${BACINTERACTOME_SHINY_APP_BASE_URL}?protein=${uniprot_id}&species=${species_name}`;

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
  NAV: 0.8,
  DEFAULT: 3,
} as const;

// Essentiality Color and Icon Mapping
export const getColorForEssentiality = (essentiality: string): string => {
  switch (essentiality) {
    case 'essential':
      return '#FF0000'; // Red (critical importance)
    case 'essential_liquid':
      return '#1E90FF'; // Dodger Blue (fluid and vibrant for liquid)
    case 'essential_solid':
      return '#8B4513'; // Saddle Brown (earthy, solid representation)
    case 'not_essential':
      return '#555555'; // Dark Gray (subdued and non-critical)
    case 'unclear':
      return '#808080'; // Medium Gray (neutral and ambiguous)
    default:
      return '#DAA520'; // Goldenrod (fallback color)
  }
};

export const getIconForEssentiality = (essentiality: string) => {
  switch (essentiality) {
    case 'essential':
      return '🧪🧫'; // Test Tube + Petri Dish (U+1F9EA U+1F9EB)
    case 'essential_liquid':
      return '🧪'; // Test Tube (U+1F9EA)
    case 'essential_solid':
      return '🧫'; // Petri Dish (U+1F9EB)
    case 'not_essential':
      return '⛔'; // No Entry Sign (U+26D4)
    case 'unclear':
    default:
      return '❓'; // Question Mark (U+2753)
  }
};


export const renderExternalDbLinks = (dbType: keyof typeof EXTERNAL_DB_URLS, ids: string[] | string): React.ReactNode => {
    if (!ids || (Array.isArray(ids) && ids.length === 0)) {
        return '---';
    }

    const idArray = Array.isArray(ids) ? ids : [ids];

    return idArray.map((id, index) => {
        const trimmedId = id.trim();
        if (!trimmedId || trimmedId === '---') {
            return null;
        }

        const link = generateExternalDbLink(dbType, trimmedId);

        return (
            <React.Fragment key={`${dbType}-${trimmedId}-${index}`}>
                <a
                    href={link}
                    target="_blank"
                    rel="noopener noreferrer"
                    title={`View ${trimmedId} in ${dbType}`}
                    style={{ color: '#007bff', textDecoration: 'none' }}
                    onMouseEnter={(e) => {
                        e.currentTarget.style.textDecoration = 'underline';
                    }}
                    onMouseLeave={(e) => {
                        e.currentTarget.style.textDecoration = 'none';
                    }}
                >
                    {trimmedId}
                </a>
                {index < idArray.length - 1 && ', '}
            </React.Fragment>
        );
    }).filter(Boolean);
};


