import {ApiService} from "./api";
import {Gene, GeneEssentialityTag, GeneMeta, GeneSuggestion, PaginatedResponse} from "../interfaces/Gene";
import {cacheResponse} from "./cachingDecorator";

export class GeneService {
    /**
     * Utility method to build query parameters.
     */
    private static buildParams(
        query: string,
        page: number = 1,
        perPage: number = 10,
        speciesId?: number,
        genomeIds?: string
    ): URLSearchParams {
        return new URLSearchParams({
            query,
            page: String(page),
            per_page: String(perPage),
            ...(speciesId && {species_id: String(speciesId)}),
            ...(genomeIds && {genome_ids: genomeIds}),
        });
    }

    /**
     * Fetch gene autocomplete suggestions.
     */
    static async fetchGeneAutocompleteSuggestions(
        query: string,
        limit: number = 10,
        speciesId?: number,
        genomeIds?: string,
        essentialityFilter?: string[]
    ): Promise<GeneSuggestion[]> {
        try {
            const params = this.buildParams(query, 1, limit, speciesId, genomeIds);
            if (essentialityFilter && essentialityFilter.length > 0) {
                const filterValue = `essentiality:${essentialityFilter.join(",")}`;
                params.append("filter", filterValue);
            }
            const response = await ApiService.get<GeneSuggestion[]>("genes/autocomplete", params);
            return response;
        } catch (error) {
            console.error("Error fetching gene autocomplete suggestions:", error);
            throw error;
        }
    }

    /**
     * Fetch gene search results with advanced filters.
     */
    static async fetchGeneSearchResults(
        gene: string,
        page: number,
        perPage: number,
        sortField: string,
        sortOrder: string,
        selectedGenomes?: { id: number; name: string }[],
        selectedSpecies?: number[],
        essentialityFilter?: string[]
    ): Promise<PaginatedResponse<GeneMeta>> {
        try {
            const params = new URLSearchParams({
                query: gene,
                page: String(page),
                per_page: String(perPage),
                sort_field: sortField,
                sort_order: sortOrder,
            });

            if (selectedGenomes?.length) {
                params.append("genome_ids", selectedGenomes.map((genome) => genome.id).join(","));
            }

            if (selectedSpecies?.length === 1) {
                params.append("species_id", String(selectedSpecies[0]));
            }

            if (essentialityFilter?.length) {
                const filterValue = `essentiality:${essentialityFilter.join(",")}`;
                params.append("filter", filterValue);
            }

            const response = await ApiService.get<PaginatedResponse<GeneMeta>>("/genes/search/advanced", params);
            return response;
        } catch (error) {
            console.error("Error fetching gene search results:", error);
            throw error;
        }
    }

    /**
     * Fetch gene search results by genome ID.
     */
    static async fetchGeneBySearch(
        genomeId: number,
        query: string,
        page: number = 1
    ): Promise<PaginatedResponse<Gene>> {
        try {
            const params = new URLSearchParams({query, page: String(page)});
            const url = genomeId ? `species/${genomeId}/genomes/search` : "";
            const response = await ApiService.get<PaginatedResponse<Gene>>(url, params);
            return response;
        } catch (error) {
            console.error("Error fetching genome search results:", error);
            throw error;
        }
    }

    /**
     * Fetch genes by genome ID.
     */
    static async fetchGenesByGenome(
        genomeId: number,
        page: number = 1,
        perPage: number = 10
    ): Promise<PaginatedResponse<GeneMeta>> {
        try {
            const params = this.buildParams("", page, perPage);
            const response = await ApiService.get<PaginatedResponse<GeneMeta>>(`genomes/${genomeId}/genes`, params);
            return response;
        } catch (error) {
            console.error("Error fetching genes by genome:", error);
            throw error;
        }
    }

    /**
     * Fetch a specific gene by its ID.
     */
    static async fetchGeneById(geneId: number): Promise<GeneMeta> {
        try {
            const response = await ApiService.get<GeneMeta>(`/genes/${geneId}`);
            return response;
        } catch (error) {
            console.error(`Error fetching gene with ID ${geneId}:`, error);
            throw error;
        }
    }

    /**
     * Fetch essentiality tags with caching enabled.
     */
    @cacheResponse(60 * 60 * 1000) // Cache for 60 minutes
    static async fetchEssentialityTags(): Promise<GeneEssentialityTag[]> {
        try {
            return await ApiService.get<GeneEssentialityTag[]>(`/genes/essentiality/tags`);
        } catch (error) {
            console.error("Error fetching essentiality tags:", error);
            throw error;
        }
    }
}
