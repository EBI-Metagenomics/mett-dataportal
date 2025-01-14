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