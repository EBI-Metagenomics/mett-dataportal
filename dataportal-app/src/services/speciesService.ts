import {getData} from './api';
import apiInstance from "./apiInstance";

interface Species {
    id: number;
    scientific_name: string;
}

interface PaginatedResponse<T> {
    data: T[];
    total: number;
}

// Fetch all species data
export const fetchSpeciesList = async (): Promise<Species[]> => {
    try {
        const response = await apiInstance.get('species/');
        return response.data.map((item: any) => ({
            id: item.id,
            scientific_name: item.scientific_name || item.name // Map the API response correctly
        }));
    } catch (error) {
        console.error('Error fetching species list:', error);
        throw error;
    }
};

// Fetch isolate data filtered by species if provided
export const fetchIsolateList = async (speciesId?: string): Promise<PaginatedResponse<Species>> => {
    const url = speciesId
        ? `/api/isolates?species=${speciesId}` // Fetch isolates by species
        : '/api/isolates'; // Fetch all isolates
    try {
        const response = await apiInstance.get(url);
        return response.data;
    } catch (error) {
        console.error('Error fetching isolates:', {speciesId, error});
        throw error;
    }
};
