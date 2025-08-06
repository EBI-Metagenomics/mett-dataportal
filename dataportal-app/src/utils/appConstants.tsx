import React from 'react';

export const ZOOM_LEVELS = {
    MIN: -2,
    MAX: 5,
    NAV: 0.8,
    DEFAULT: 3,
};

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
export const API_GENOMES_BY_ISOLATE_NAMES = `${API_BASE_URL}/genomes/by-isolate-names`;

export const EXTERNAL_DB_URLS = {
    PFAM: import.meta.env.VITE_PFAM_URL || 'https://www.ebi.ac.uk/interpro/entry/pfam/',
    INTERPRO: import.meta.env.VITE_INTERPRO_URL || 'https://www.ebi.ac.uk/interpro/entry/',
    KEGG: import.meta.env.VITE_KEGG_URL || 'https://www.genome.jp/entry/',
    COG: import.meta.env.VITE_COG_URL || 'https://www.ncbi.nlm.nih.gov/research/cog/cog/',
};

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
        default:
            return `${baseUrl}${id}`;
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

export const BACINTERACTOME_SHINY_APP_BASE_URL = import.meta.env.VITE_BACINTERACTOME_SHINY_APP_URL;
export const getBacinteractomeUniprotUrl =
    (uniprot_id: string, species_name: string) => `${BACINTERACTOME_SHINY_APP_BASE_URL}?protein=${uniprot_id}&species=${species_name}`;

export const getAPIUrlGenomeSearchWithSpecies =
    (species_acronym: string) => `${API_BASE_URL}/species/${species_acronym}/genomes/search`;
export const API_GENOME_SEARCH = `${API_BASE_URL}/genomes/search`;
export const getEssentialityDataUrl = (isolate_name: string) => `${API_BASE_URL}/genomes/${isolate_name}/essentiality`;

export const API_GENE_SEARCH_ADVANCED = `${API_BASE_URL}/genes/search/advanced`;

export const EBI_FTP_SERVER = "https://ftp.ebi.ac.uk/pub/databases/mett/";
export const EXT_LINK_ESSENTIALITY_JOURNAL = "https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1004401";
export const ESSENTIALITY_DETERMINATION_TXT = "Gene essentiality was determined by analyzing transposon insertion\n" +
    "                                                    libraries using the software package TRANSIT (DeJesus et al. 2015).\n" +
    "                                                    Libraries were created using a Mariner transposon and by outgrowth\n" +
    "                                                    of mutants in either liquid or solid mGAM (rich undefined) culture\n" +
    "                                                    media.";

export const AMR_DETERMINATION_TXT = "Antimicrobial resistance (AMR) information was determined using AMRFinderPlus.";
export const EXT_LINK_AMR_DETERMINATION = "https://github.com/ncbi/amr";

export const SPINNER_DELAY = 200;
export const DEFAULT_PER_PAGE_CNT = 10;
export const FACET_INITIAL_VISIBLE_CNT = 10;
export const FACET_STEP_CNT = 10;
export const TABLE_MAX_COLUMNS = 15;

// Example sequence constant
export const EXAMPLE_SEQUENCE = `>Example protein sequence\nMSEIDHVGLWNRCLEIIRDNVPEQTYKTWFLPIIPLKYEDKTLV`;

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


export const DISPLAY_SETTINGS = {
    DEFAULT_BUFFER: 10000,
};

export const getColorForEssentiality = (essentiality: string): string => {
    switch (essentiality) {
        case 'essential':
            return '#FF0000'; // Red (critical importance)
        // return '#FFD700'; // Gold (matches the star)
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


