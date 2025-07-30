export const ZOOM_LEVELS = {
    MIN: -2,
    MAX: 5,
    NAV: 0.8,
    DEFAULT: 3,
};

export const API_BASE_URL = 'http://localhost:8000/api';
export const API_GENOMES_BY_ISOLATE_NAMES = `${API_BASE_URL}/genomes/by-isolate-names`;

export const BACINTERACTOME_SHINY_APP_BASE_URL = 'http://localhost:3838';
export const getBacinteractomeUniprotUrl = (uniprot_id: string, species_name: string) => `${BACINTERACTOME_SHINY_APP_BASE_URL}?protein=${uniprot_id}&species=${species_name}`;

export const getAPIUrlGenomeSearchWithSpecies = (species_acronym: string) => `${API_BASE_URL}/species/${species_acronym}/genomes/search`;
export const API_GENOME_SEARCH = `${API_BASE_URL}/genomes/search`;
export const getEssentialityDataUrl = (isolate_name: string) => `${API_BASE_URL}/genomes/${isolate_name}/essentiality`;

export const API_GENE_SEARCH_ADVANCED = `${API_BASE_URL}/genes/search/advanced`;

export const EBI_FTP_SERVER = "https://ftp.ebi.ac.uk/pub/databases/mett/";
export const EXT_LINK_ESSENTIALITY_JOURNAL = "https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1004401";
export const ESSENTIALITY_DETERMINATION_TXT = "Gene essentiality was determined by analyzing transposon insertion libraries using the software package TRANSIT (DeJesus et al. 2015).";

export const AMR_DETERMINATION_TXT = "Antimicrobial resistance (AMR) information was determined using AMRFinderPlus.";
export const EXT_LINK_AMR_DETERMINATION = "https://github.com/ncbi/amr";

export const SPINNER_DELAY = 200;
export const DEFAULT_PER_PAGE_CNT = 10;
export const FACET_INITIAL_VISIBLE_CNT = 10;
export const FACET_STEP_CNT = 10;
export const TABLE_MAX_COLUMNS = 15;

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
            return '#FF0000';
        case 'essential_liquid':
            return '#1E90FF';
        case 'essential_solid':
            return '#8B4513';
        case 'not_essential':
            return '#555555';
        case 'unclear':
            return '#808080';
        default:
            return '#DAA520';
    }
};

export const getIconForEssentiality = (essentiality: string) => {
    switch (essentiality) {
        case 'essential':
            return '🧪🧫';
        case 'essential_liquid':
            return '🧪';
        case 'essential_solid':
            return '🧫';
        case 'not_essential':
            return '⛔';
        case 'unclear':
        default:
            return '❓';
    }
}; 