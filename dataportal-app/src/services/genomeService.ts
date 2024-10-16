import {getData} from './api';
import apiInstance from "./apiInstance";

// Fetch genomes based on species and genome query
export const fetchGenomesBySearch = async (species: number[], genome: string, page: number = 1): Promise<any> => {
    try {
        let url = '';
        const params: any = {query: genome, page};

        if (species.length === 1) {
            // If only one species is selected, call the species-specific endpoint
            const speciesId = species[0];
            url = `species/${speciesId}/genomes/search`;
        } else {
            // If multiple species or none are selected, call the default genome search endpoint
            url = `genomes/search`;
        }
        return await getData(url, params);
    } catch (error) {
        console.error('Error fetching genome search results:', error);
        throw error;
    }
};


// Fetch isolate suggestions with optional species ID
export const fetchFuzzyIsolateSuggestions = async (query: string, speciesId?: string) => {
    try {
        const params: any = {query};

        // Include speciesId if provided
        if (speciesId) {
            params.species_id = speciesId;
        }

        const response = await apiInstance.get('genomes/search/autocomplete', {params});
        return response.data;
    } catch (error) {
        console.error('Error fetching isolate suggestions:', error);
        throw error;
    }
};

// Fetch all isolates or isolates filtered by species ID
export const fetchIsolatesBySpecies = async (speciesId?: string) => {
    try {
        const params = speciesId ? {species_id: speciesId} : {};
        const response = await apiInstance.get('species/isolates', {params});
        return response.data;
    } catch (error) {
        console.error('Error fetching isolates:', error);
        throw error;
    }
};

// Fetch all type strains
export const fetchTypeStrains = async (): Promise<any> => {
    try {
        const response = await apiInstance.get('/genomes/type-strains');
        return response.data;
    } catch (error) {
        console.error('Error fetching type strains:', error);
        throw error;
    }
};

