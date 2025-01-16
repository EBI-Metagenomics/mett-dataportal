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
            return '#FF0000'; // Red
        case 'not_essential':
            return '#008000'; // Green
        case 'essential_liquid':
            return '#FFA500'; // Orange
        case 'essential_solid':
            return '#800080'; // Purple
        case 'unclear':
            return '#808080'; // Gray
        default:
            return '#DAA520'; // Goldenrod
    }
};

export const getIconForEssentiality = (essentiality: string) => {
    switch (essentiality) {
        case 'essential':
            return '💎'; // Gem for essential
        case 'not_essential':
            return '🍂'; // Fallen leaf for not essential
        case 'essential_liquid':
            return '💧'; // Droplet for liquid
        case 'essential_solid':
            return '🧊'; // Ice cube for solid
        case 'unclear':
        default:
            return '🌀'; // Cyclone for unclear
    }
};
