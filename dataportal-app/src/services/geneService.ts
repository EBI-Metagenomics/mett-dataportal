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
        speciesAcronym?: string,
        genomeIds?: string
    ): URLSearchParams {
        return new URLSearchParams({
            query,
            page: String(page),
            per_page: String(perPage),
            ...(speciesAcronym && {species_acronym: String(speciesAcronym)}),
            ...(genomeIds && {isolates: genomeIds}),
        });
    }

    /**
     * Fetch gene autocomplete suggestions.
     */
    static async fetchGeneAutocompleteSuggestions(
        query: string,
        limit: number = 10,
        speciesAcronym?: string,
        genomeIds?: string,
        essentialityFilter?: string[]
    ): Promise<GeneSuggestion[]> {
        try {
            const params = this.buildParams(query, 1, limit, speciesAcronym, genomeIds);
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
    static async fetchGeneSearchResultsAdvanced(
        query: string,
        page: number,
        perPage: number,
        sortField: string,
        sortOrder: string,
        selectedGenomes?: { isolate_name: string; type_strain: boolean }[],
        selectedSpecies?: string[],
        essentialityFilter?: string[]
    ): Promise<PaginatedResponse<GeneMeta>> {
        try {
            const params = GeneService.buildParamsFetchGeneSearchResults(query, page, perPage, sortField, sortOrder, selectedGenomes, selectedSpecies, essentialityFilter);
            const response = await ApiService.get<PaginatedResponse<GeneMeta>>("/genes/search/advanced", params);
            return response;
        } catch (error) {
            console.error("Error fetching gene search results:", error);
            throw error;
        }
    }

    static buildParamsFetchGeneSearchResults(
        gene: string,
        page: number,
        perPage: number,
        sortField: string,
        sortOrder: string,
        selectedGenomes?: { isolate_name: string; type_strain: boolean }[],
        selectedSpecies?: string[],
        essentialityFilter?: string[]
    ) {
        const params = new URLSearchParams({
            query: gene,
            page: String(page),
            per_page: String(perPage),
            sort_field: sortField,
            sort_order: sortOrder,
        });

        if (selectedGenomes?.length) {
            params.append("isolates", selectedGenomes.map((genome) => genome.isolate_name).join(","));
        }

        if (selectedSpecies?.length === 1) {
            params.append("species_acronym", String(selectedSpecies[0]));
        }

        if (essentialityFilter?.length) {
            const filterValue = `essentiality:${essentialityFilter.join(",")}`;
            params.append("filter", filterValue);
        }
        return params;
    }

    /**
     * Fetch gene search results by genome ID.
     */
    static async fetchGeneBySearch(
        genomeId: string,
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
        isolate_name: string,
        page: number = 1,
        perPage: number = 10
    ): Promise<PaginatedResponse<GeneMeta>> {
        try {
            const params = this.buildParams("", page, perPage);
            const response = await ApiService.get<PaginatedResponse<GeneMeta>>(`genomes/${isolate_name}/genes`, params);
            return response;
        } catch (error) {
            console.error("Error fetching genes by genome:", error);
            throw error;
        }
    }

    /**
     * Fetch a specific gene by its ID.
     */
    static async fetchGeneByLocusTag(locus_tag: string): Promise<GeneMeta> {
        try {
            const response = await ApiService.get<GeneMeta>(`/genes/${locus_tag}`);
            return response;
        } catch (error) {
            console.error(`Error fetching gene with locus tag ${locus_tag}:`, error);
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

    @cacheResponse(60 * 60 * 1000) // Cache for 60 minutes
    static async fetchEssentialityData(apiUrl: string, refName: string): Promise<Record<string, any>> {
        // Fetch data from the API if not in the cache
        try {
            const response = await fetch(`${apiUrl}/${refName}`);
            if (!response.ok) {
                throw new Error(`Failed to fetch essentiality data for ${refName}`);
            }

            const data = await response.json();

            return data;
        } catch (error) {
            console.error(`Error fetching essentiality data for ${refName}:`, error);
            return {};
        }
    }
}
