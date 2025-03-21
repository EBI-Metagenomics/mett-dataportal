export const ZOOM_LEVELS = {
    MIN: -2,
    MAX: 5,
    NAV:-2,
    DEFAULT: 2,
};

export const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api';
export const API_GENOMES_BY_ISOLATE_NAMES = `${API_BASE_URL}/genomes/by-isolate-names`;
export const getAPIUrlGenomeSearchWithSpecies = (species_acronym: string) => `${API_BASE_URL}/species/${species_acronym}/genomes/search`;
export const API_GENOME_SEARCH = `${API_BASE_URL}/genomes/search`;
export const getEssentialityDataUrl = (isolate_name: string) => `${API_BASE_URL}/genomes/${isolate_name}/essentiality`;

export const API_GENE_SEARCH_ADVANCED = `${API_BASE_URL}/genes/search/advanced`;

export const SPINNER_DELAY = 200; // Configurable delay in milliseconds

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


