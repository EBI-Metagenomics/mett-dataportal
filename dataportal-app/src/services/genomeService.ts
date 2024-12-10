import {getData} from './api';
import apiInstance from "./apiInstance";
import {GenomeMeta, GenomeResponse} from "@components/interfaces/Genome";

interface AutocompleteResponse {
    data: string[];
}

export const fetchGenomeAutocompleteSuggestions = async (inputQuery: string, selectedSpecies?: string) => {
    try {
        const url = selectedSpecies
            ? `/genomes/autocomplete?query=${encodeURIComponent(inputQuery)}&species_id=${selectedSpecies}`
            : `/genomes/autocomplete?query=${encodeURIComponent(inputQuery)}`;

        const response = await getData(url);
        return response;
    } catch (error) {
        console.error('Error fetching genome suggestions:', error);
        throw error;
    }
};

export const fetchGenomeByStrainIds = async (strainIds: number[]) => {
    try {
        const response = await getData(`/genomes/by-ids?ids=${strainIds}`);
        return response;
    } catch (error) {
        console.error(`Error fetching genome with strain IDs ${strainIds}:`, error);
        throw error;
    }
};

export const fetchGenomeByIsolateNames = async (isolateNames: string[]) => {
    try {
        const response = await getData(`/genomes/by-isolate-names?names=${isolateNames}`);
        return response;
    } catch (error) {
        console.error(`Error fetching genome by isolate names ${isolateNames}:`, error);
        throw error;
    }
};

export const fetchGenomeSearchResults = async (
    query: string,
    page: number,
    pageSize: number,
    sortField: string,
    sortOrder: string,
    selectedSpecies?: number []
) => {
    const queryString = new URLSearchParams({
        'query': query,
        'page': String(page),
        'per_page': String(pageSize),
        'sortField': sortField,
        'sortOrder': sortOrder
    }).toString();

    const endpoint = (selectedSpecies && selectedSpecies.length === 1)
        ? `/species/${selectedSpecies[0]}/genomes/search?${queryString}`
        : `/genomes/search?${queryString}`;

    try {
        const response = await getData(endpoint);
        return response;
    } catch (error) {
        console.error('Error fetching genome search results:', error);
        throw error;
    }
};

// Fetch genomes based on species and genome query
export const fetchGenomesBySearch = async (
    species: number[],
    genome: string,
    sortField: string,
    sortOrder: string
): Promise<GenomeResponse> => {
    try {
        // Initialize the base URL and query parameters
        const baseUrl = species.length === 1 ? `species/${species[0]}/genomes/search` : `genomes/search`;

        // Construct query parameters
        const params = new URLSearchParams({
            query: genome,
            sortField,
            sortOrder,
        });

        // Make API request with the constructed URL and parameters
        const response = await apiInstance.get(`${baseUrl}?${params.toString()}`);

        return response.data;
    } catch (error) {
        console.error('Error fetching genome search results:', {
            species,
            genome,
            sortField,
            sortOrder,
            error,
        });
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

// Fetch all type strains
export const fetchTypeStrains = async (): Promise<GenomeMeta[]> => {
    try {
        const response = await apiInstance.get('/genomes/type-strains');
        return response.data;
    } catch (error) {
        console.error('Error fetching type strains:', error);
        throw error;
    }
};
