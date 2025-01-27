export const ZOOM_LEVELS = {
    MIN: 1,
    MAX: 5,
    DEFAULT: 2,
};

export const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api';
export const getEssentialityDataUrl = (strainId: number) => `${API_BASE_URL}/genomes/${strainId}/essentiality`;

export const DISPLAY_SETTINGS = {
    DEFAULT_BUFFER: 10000,
};

export const getColorForEssentiality = (essentiality: string): string => {
    switch (essentiality) {
        case 'essential':
            return '#FF0000'; // Red (critical importance)
        case 'not_essential':
            return '#555555'; // Dark Gray (subdued and non-critical)
        case 'essential_liquid':
            return '#1E90FF'; // Dodger Blue (fluid and vibrant for liquid)
        case 'essential_solid':
            return '#8B4513'; // Saddle Brown (earthy, solid representation)
        case 'unclear':
            return '#808080'; // Medium Gray (neutral and ambiguous)
        default:
            return '#DAA520'; // Goldenrod (fallback color)
    }
};

export const getIconForEssentiality = (essentiality: string) => {
    switch (essentiality) {
        case 'essential':
            return '♦️'; // Gem
        case 'not_essential':
            return '⚫'; // Black Circle (minimal and understated)
        case 'essential_liquid':
            return '💎'; // Gem \
        case 'essential_solid':
            return '🔶'; // Rock (stable and earthy)
        case 'unclear':
        default:
            return '🌫️'; // Fog (unclear and ambiguous)
    }
};
