import {getData} from './api';
import apiInstance from "./apiInstance";

interface Genome {
    id: number;
    isolate_name: string;
}

interface AutocompleteResponse {
    data: string[];
}

interface PaginatedResponse<T> {
    data: T[];
    total: number;
}


// Fetch genomes based on species and genome query
export const fetchGenomesBySearch = async (
    species: number[],
    genome: string
): Promise<Genome[]> => {
    try {
        let url = '';
        const params: any = { query: genome };

        if (species.length === 1) {
            // If only one species is selected, call the species-specific endpoint
            url = `species/${species[0]}/genomes/search`;
        } else {
            // Call default genome search endpoint
            url = `genomes/search`;
        }

        const response = await apiInstance.get(url, { params });
        return response.data; // Assume response is an array of genomes
    } catch (error) {
        console.error('Error fetching genome search results:', { species, genome, error });
        throw error;
    }
};

// Fetch isolate suggestions with optional species ID
export const fetchFuzzyIsolateSuggestions = async (
    query: string,
    speciesId?: string
): Promise<AutocompleteResponse> => {
    try {
        const params = {query, ...(speciesId && {species_id: speciesId})};
        const response = await apiInstance.get('genomes/search/autocomplete', {params});
        return response.data;
    } catch (error) {
        console.error('Error fetching isolate suggestions:', {query, speciesId, error});
        throw error;
    }
};

// Fetch isolates filtered by species if provided
export const fetchIsolatesBySpecies = async (
    speciesId?: string
): Promise<PaginatedResponse<Genome>> => {
    try {
        const params = speciesId ? {species_id: speciesId} : {};
        const response = await apiInstance.get('species/isolates', {params});
        return response.data;
    } catch (error) {
        console.error('Error fetching isolates:', {speciesId, error});
        throw error;
    }
};

// Fetch all type strains
export const fetchTypeStrains = async (): Promise<Genome[]> => {
    try {
        const response = await apiInstance.get('/genomes/type-strains');
        return response.data.map((item: any) => ({
            id: item.id,
            isolate_name: item.isolate_name || item.name // Map the API response correctly
        }));
    } catch (error) {
        console.error('Error fetching type strains:', error);
        throw error;
    }
};
