export const ZOOM_LEVELS = {
    MIN: 1,
    MAX: 5,
    DEFAULT: 2,
};

export const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api';
export const API_GENOMES_BY_IDS = `${API_BASE_URL}/genomes/by-ids`;
export const getAPIUrlGenomeSearchWithSpecies = (speciesId: number) => `${API_BASE_URL}/species/${speciesId}/genomes/search`;
export const API_GENOME_SEARCH = `${API_BASE_URL}/genomes/search`;
export const getEssentialityDataUrl = (strainId: number) => `${API_BASE_URL}/genomes/${strainId}/essentiality`;

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
            return '⭐'; // Star (distinct shape)
        case 'essential_liquid':
            return '💧'; // Droplet (represents liquid)
        case 'essential_solid':
            return '🪨'; // Rock (brown, represents solid)
        case 'not_essential':
            return '⚫'; // Black Circle
        case 'unclear':
        default:
            return '🌫️'; // Fog
    }
};

