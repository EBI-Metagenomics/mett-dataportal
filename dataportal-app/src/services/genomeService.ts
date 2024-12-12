import {ApiService} from "./api";
import {GenomeMeta, GenomeResponse} from "../interfaces/Genome";

interface AutocompleteResponse {
    data: string[];
}

export class GenomeService {
    /**
     * Fetch genome autocomplete suggestions.
     */
    static async fetchGenomeAutocompleteSuggestions(inputQuery: string, selectedSpecies?: string) {
        try {
            const params = new URLSearchParams({
                query: inputQuery,
                ...(selectedSpecies && { species_id: selectedSpecies }),
            });
            const response = await ApiService.get("/genomes/autocomplete", params);
            return response;
        } catch (error) {
            console.error("Error fetching genome suggestions:", error);
            throw error;
        }
    }

    /**
     * Fetch genomes by strain IDs.
     */
    static async fetchGenomeByStrainIds(strainIds: number[]) {
        try {
            const params = new URLSearchParams({ ids: strainIds.join(",") });
            const response = await ApiService.get("/genomes/by-ids", params);
            return response;
        } catch (error) {
            console.error(`Error fetching genome with strain IDs ${strainIds}:`, error);
            throw error;
        }
    }

    /**
     * Fetch genomes by isolate names.
     */
    static async fetchGenomeByIsolateNames(isolateNames: string[]) {
        try {
            const params = new URLSearchParams({ names: isolateNames.join(",") });
            const response = await ApiService.get("/genomes/by-isolate-names", params);
            return response;
        } catch (error) {
            console.error(`Error fetching genome by isolate names ${isolateNames}:`, error);
            throw error;
        }
    }

    /**
     * Fetch genome search results with optional species filter.
     */
    static async fetchGenomeSearchResults(
        query: string,
        page: number,
        pageSize: number,
        sortField: string,
        sortOrder: string,
        selectedSpecies?: number[]
    ) {
        try {
            const params = new URLSearchParams({
                query,
                page: String(page),
                per_page: String(pageSize),
                sortField,
                sortOrder,
            });

            const endpoint =
                selectedSpecies && selectedSpecies.length === 1
                    ? `/species/${selectedSpecies[0]}/genomes/search`
                    : `/genomes/search`;

            const response = await ApiService.get(endpoint, params);
            return response;
        } catch (error) {
            console.error("Error fetching genome search results:", error);
            throw error;
        }
    }

    /**
     * Fetch genomes by search query and species filter.
     */
    static async fetchGenomesBySearch(
        species: number[],
        genome: string,
        sortField: string,
        sortOrder: string
    ): Promise<GenomeResponse> {
        try {
            const baseUrl = species.length === 1 ? `species/${species[0]}/genomes/search` : `genomes/search`;

            const params = new URLSearchParams({
                query: genome,
                sortField,
                sortOrder,
            });

            const response = await ApiService.get(baseUrl, params);
            return response;
        } catch (error) {
            console.error("Error fetching genome search results:", {
                species,
                genome,
                sortField,
                sortOrder,
                error,
            });
            throw error;
        }
    }

    /**
     * Fetch fuzzy isolate suggestions with optional species ID.
     */
    static async fetchFuzzyIsolateSuggestions(query: string, speciesId?: string): Promise<AutocompleteResponse> {
        try {
            const params = new URLSearchParams({
                query,
                ...(speciesId && { species_id: speciesId }),
            });
            const response = await ApiService.get("genomes/search/autocomplete", params);
            return response;
        } catch (error) {
            console.error("Error fetching isolate suggestions:", { query, speciesId, error });
            throw error;
        }
    }

    /**
     * Fetch all type strains.
     */
    static async fetchTypeStrains(): Promise<GenomeMeta[]> {
        try {
            const response = await ApiService.get("/genomes/type-strains");
            return response;
        } catch (error) {
            console.error("Error fetching type strains:", error);
            throw error;
        }
    }
}
