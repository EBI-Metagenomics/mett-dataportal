import apiInstance from "./apiInstance";

// Fetch gene autocomplete suggestions
export const fetchGeneAutocompleteSuggestions = async (query: string, limit: number = 10, speciesId?: number, genomeIds?: string) => {
    try {
        const response = await apiInstance.get('genes/autocomplete', {
            params: {
                query,
                limit,
                species_id: speciesId,
                genome_ids: genomeIds,
            },
        });
        return response.data;
    } catch (error) {
        console.error('Error fetching gene autocomplete suggestions:', error);
        throw error;
    }
};


// Fetch genes based on genome ID
export const fetchGenesByGenome = async (genomeId: number, page: number = 1, perPage: number = 10) => {
    try {
        const response = await apiInstance.get(`genomes/${genomeId}/genes`, {
            params: {page, per_page: perPage},
        });
        return response.data;
    } catch (error) {
        console.error('Error fetching genes by genome:', error);
        throw error;
    }
};

// Search genes across multiple genome IDs
export const searchGenesAcrossGenomes = async (genomeIds: string, query: string, page: number = 1, perPage: number = 10) => {
    try {
        const response = await apiInstance.get('genes/search/filter', {
            params: {genome_ids: genomeIds, query, page, per_page: perPage},
        });
        return response.data;
    } catch (error) {
        console.error('Error searching genes across genomes:', error);
        throw error;
    }
};

// Fetch a specific gene by its ID
export const fetchGeneById = async (geneId: number) => {
    try {
        const response = await apiInstance.get(`genes/${geneId}`);
        return response.data;
    } catch (error) {
        console.error(`Error fetching gene with ID ${geneId}:`, error);
        throw error;
    }
};
