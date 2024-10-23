import apiInstance from "./apiInstance";
import { getData } from "./api";

// Define types/interfaces for better type safety
interface Gene {
    id: number;
    name: string;
    description: string;
    // other relevant fields
}

interface AutocompleteResponse {
    suggestions: { gene_id: number; strain_name: string; gene_name: string }[];
}

interface PaginatedResponse<T> {
    results: T[];
    num_pages: number;
}

// Utility function to build params
const buildParams = (query: string, page: number = 1, perPage: number = 10, speciesId?: number, genomeIds?: string) => ({
    query,
    page,
    per_page: perPage,
    species_id: speciesId,
    genome_ids: genomeIds
});

// Fetch gene autocomplete suggestions
export const fetchGeneAutocompleteSuggestions = async (
    query: string,
    limit: number = 10,
    speciesId?: number,
    genomeIds?: string
): Promise<{ gene_id: number; strain_name: string; gene_name: string }[]> => {
    try {
        const response = await apiInstance.get('genes/autocomplete', {
            params: buildParams(query, 1, limit, speciesId, genomeIds)
        });
        return response.data; // Return only response data
    } catch (error) {
        console.error('Error fetching gene autocomplete suggestions:', { query, speciesId, genomeIds, error });
        throw error;
    }
};

// Fetch gene search results by genome ID
export const fetchGeneBySearch = async (
    genomeId: number,
    query: string,
    page: number = 1
): Promise<PaginatedResponse<Gene>> => {
    try {
        const url = genomeId ? `species/${genomeId}/genomes/search` : '';
        const response = await getData(url, { query, page });
        return {
            results: response.data, // Accessing the results from response data
            num_pages: response.num_pages || 1 // Access num_pages from the data
        };
    } catch (error) {
        console.error('Error fetching genome search results:', { genomeId, query, page, error });
        throw error;
    }
};

// Fetch genes by genome ID
export const fetchGenesByGenome = async (
    genomeId: number,
    page: number = 1,
    perPage: number = 10
): Promise<PaginatedResponse<Gene>> => {
    try {
        const response = await apiInstance.get(`genomes/${genomeId}/genes`, {
            params: buildParams('', page, perPage)
        });
        return {
            results: response.data, // Accessing the results from response data
            num_pages: response.data.num_pages || 1 // Access num_pages from response data
        };
    } catch (error) {
        console.error('Error fetching genes by genome:', { genomeId, page, perPage, error });
        throw error;
    }
};

// Search genes across multiple genome IDs
export const searchGenesAcrossGenomes = async (
    genomeIds: string,
    query: string,
    page: number = 1,
    perPage: number = 10
): Promise<PaginatedResponse<Gene>> => {
    try {
        const response = await apiInstance.get('genes/search/filter', {
            params: buildParams(query, page, perPage, undefined, genomeIds)
        });
        return {
            results: response.data, // Accessing the results from response data
            num_pages: response.data.num_pages || 1 // Access num_pages from response data
        };
    } catch (error) {
        console.error('Error searching genes across genomes:', { genomeIds, query, page, perPage, error });
        throw error;
    }
};

// Fetch a specific gene by its ID
export const fetchGeneById = async (geneId: number): Promise<Gene> => {
    try {
        const response = await apiInstance.get(`genes/${geneId}`);
        return response.data;
    } catch (error) {
        console.error(`Error fetching gene with ID ${geneId}:`, error);
        throw error;
    }
};
