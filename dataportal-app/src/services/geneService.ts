import {ApiService} from "./api";
import {Gene, GeneFacetResponse, GeneMeta, GeneProteinSeq, GeneSuggestion, PaginatedResponse} from "../interfaces/Gene";
import {cacheResponse} from "./cachingDecorator";
import {DEFAULT_PER_PAGE_CNT} from "../utils/appConstants";

export class GeneService {
    /**
     * Utility method to build query parameters.
     */
    private static buildParams(
        query: string,
        page: number = 1,
        perPage: number = DEFAULT_PER_PAGE_CNT,
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
        limit: number = DEFAULT_PER_PAGE_CNT,
        speciesAcronym?: string,
        genomeIds?: string,
        selectedFacets?: Record<string, string[]>
    ): Promise<GeneSuggestion[]> {
        try {
            const params = this.buildParams(query, 1, limit, speciesAcronym, genomeIds);
            if (selectedFacets) {
                const filterParts: string[] = [];

                for (const [key, values] of Object.entries(selectedFacets)) {
                    if (values.length > 0) {
                        filterParts.push(`${key}:${values.join(",")}`);
                    }
                }

                if (filterParts.length > 0) {
                    params.append("filter", filterParts.join(";"));
                }
            }
            const response = await ApiService.get<GeneSuggestion[]>("genes/autocomplete", params);
            // console.log("****response", response)
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
        selectedFacets?: Record<string, string[]>,
        facetOperators?: Record<string, 'AND' | 'OR'>
    ): Promise<PaginatedResponse<GeneMeta>> {
        try {
            // console.log("####query: ", query)
            const params =
                GeneService.buildParamsFetchGeneSearchResults(
                    query, page, perPage, sortField, sortOrder,
                    selectedGenomes, selectedSpecies, selectedFacets, facetOperators);
            const response = await ApiService.get<PaginatedResponse<GeneMeta>>("/genes/search/advanced", params);
            return response;
        } catch (error) {
            console.error("Error fetching gene search results:", error);
            throw error;
        }
    }

    static buildParamsFetchGeneSearchResults(
        query: string,
        page: number,
        perPage: number,
        sortField: string,
        sortOrder: string,
        selectedGenomes?: { isolate_name: string; type_strain: boolean }[],
        selectedSpecies?: string[],
        selectedFacets?: Record<string, string[]>,
        facetOperators?: Record<string, 'AND' | 'OR'>
    ) {
        const params = new URLSearchParams({
            query: query,
            page: String(page),
            per_page: String(perPage),
            sort_field: sortField,
            sort_order: sortOrder,
        });

        if (selectedGenomes?.length) {
            params.append("isolates", selectedGenomes.map(g => g.isolate_name).join(","));
        }

        if (selectedSpecies?.length === 1) {
            params.append("species_acronym", String(selectedSpecies[0]));
        }

        if (selectedFacets) {
            const filterParts: string[] = [];

            for (const [key, values] of Object.entries(selectedFacets)) {
                if (values.length > 0) {
                    filterParts.push(`${key}:${values.join(",")}`);
                }
            }

            if (filterParts.length > 0) {
                params.append("filter", filterParts.join(";"));
            }
        }

        if (facetOperators) {
            const filterOpParts: string[] = [];

            for (const [key, values] of Object.entries(facetOperators)) {
                if (values.length > 0) {
                    filterOpParts.push(`${key}:${values}`);
                }
            }

            if (filterOpParts.length > 0) {
                params.append("filter_operators", filterOpParts.join(";"));
            }
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
        perPage: number = DEFAULT_PER_PAGE_CNT
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
     * Fetch protein sequence information for a gene by its locus tag.
     */
    @cacheResponse(60 * 60 * 1000) // Cache for 60 minutes, uses first arg (locus_tag) as key
    static async fetchGeneProteinSeq(locus_tag: string): Promise<GeneProteinSeq> {
        try {
            const response = await ApiService.get<GeneProteinSeq>(`/genes/protein/${locus_tag}`);
            return response;
        } catch (error) {
            console.error(`Error fetching protein sequence for locus tag ${locus_tag}:`, error);
            throw error;
        }
    }

    @cacheResponse(60 * 60 * 1000, (apiUrl: string, refName: string) => `${apiUrl}:${refName}`) // Cache for 60 minutes, uses combined key
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

    /**
     * faceted search.
     */
    static async fetchGeneFacets(
        speciesAcronym?: string,
        isolates?: string,
        essentiality?: string,
        cogId?: string,
        cogFuncats?: string,
        kegg?: string,
        goTerm?: string,
        pfam?: string,
        interpro?: string,
        facetOperators?: Record<string, 'AND' | 'OR'>
    ): Promise<GeneFacetResponse> {
        try {
            const params = new URLSearchParams({
                ...(speciesAcronym && {species_acronym: speciesAcronym}),
                ...(isolates && {isolates: isolates}),
                ...(essentiality && {essentiality}),
                ...(cogId && {cog_id: cogId}),
                ...(cogFuncats && {cog_funcats: cogFuncats}),
                ...(kegg && {kegg}),
                ...(goTerm && {go_term: goTerm}),
                ...(pfam && {pfam}),
                ...(interpro && {interpro}),
                ...(facetOperators?.pfam && {pfam_operator: facetOperators.pfam}),
                ...(facetOperators?.interpro && {interpro_operator: facetOperators.interpro}),
                ...(facetOperators?.cog_id && {cog_id_operator: facetOperators.cog_id}),
                ...(facetOperators?.cog_funcats && {cog_funcats_operator: facetOperators.cog_funcats}),
                ...(facetOperators?.kegg && {kegg_operator: facetOperators.kegg}),
                ...(facetOperators?.go_term && {go_term_operator: facetOperators.go_term}),
            });

            const response = await ApiService.get<GeneFacetResponse>("genes/faceted-search", params);
            return response;
        } catch (error) {
            console.error("Error fetching gene facets:", error);
            throw error;
        }
    }
}
