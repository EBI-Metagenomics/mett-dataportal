import {ApiService} from "./api";
import {GeneFacetResponse, GeneMeta, GeneProteinSeq, GeneSuggestion, PaginatedResponse} from "../interfaces/Gene";
import {cacheResponse} from "./cachingDecorator";
import {DEFAULT_PER_PAGE_CNT} from "../utils/appConstants";

interface SearchParams {
    query?: string;
    page?: number;
    pageSize?: number;
    sortField?: string;
    sortOrder?: 'asc' | 'desc';
    species?: string[];
    genomes?: string[];
    facets?: Record<string, string[]>;
    facetOperators?: Record<string, 'AND' | 'OR'>;
}

export class GeneService {
    private static readonly API_BASE = '/api/genes';

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
            return response;
        } catch (error) {
            console.error("Error fetching gene autocomplete suggestions:", error);
            throw error;
        }
    }

    static async searchGenes(params: SearchParams): Promise<PaginatedResponse<GeneMeta>> {
        const searchParams = new URLSearchParams();

        if (params.query) {
            searchParams.set('query', params.query);
        }
        if (params.page) {
            searchParams.set('page', String(params.page));
        }
        if (params.pageSize) {
            searchParams.set('pageSize', String(params.pageSize));
        }
        if (params.sortField) {
            searchParams.set('sortField', params.sortField);
        }
        if (params.sortOrder) {
            searchParams.set('sortOrder', params.sortOrder);
        }
        if (params.species?.length) {
            searchParams.set('species', params.species.join(','));
        }
        if (params.genomes?.length) {
            searchParams.set('genomes', params.genomes.join(','));
        }
        if (params.facets) {
            Object.entries(params.facets).forEach(([group, values]) => {
                if (values.length > 0) {
                    searchParams.set(`facets.${group}`, values.join(','));
                }
            });
        }
        if (params.facetOperators) {
            searchParams.set('facetOperators', JSON.stringify(params.facetOperators));
        }

        const response = await ApiService.get<PaginatedResponse<GeneMeta>>("/genes/search/advanced", searchParams);
        if (!response) {
            throw new Error('Failed to fetch genes');
        }

        return response;
    }

    static async fetchFacets(params: SearchParams): Promise<GeneFacetResponse> {
        const searchParams = new URLSearchParams();

        if (params.species?.length) {
            searchParams.set('species_acronym', params.species[0]); // Only use first species
        }
        if (params.genomes?.length) {
            searchParams.set('isolates', params.genomes.join(','));
        }
        if (params.facets) {
            // Map facet values to their respective parameters
            Object.entries(params.facets).forEach(([group, values]) => {
                if (values.length > 0) {
                    switch (group) {
                        case 'cog_id':
                            searchParams.set('cog_id', values.join(','));
                            break;
                        case 'cog_funcats':
                            searchParams.set('cog_funcats', values.join(','));
                            break;
                        case 'kegg':
                            searchParams.set('kegg', values.join(','));
                            break;
                        case 'pfam':
                            searchParams.set('pfam', values.join(','));
                            break;
                        case 'interpro':
                            searchParams.set('interpro', values.join(','));
                            break;
                        case 'essentiality':
                            searchParams.set('essentiality', values[0]); // Only use first value
                            break;
                        case 'has_amr_info':
                            searchParams.set('has_amr_info', values[0]); // Only use first value
                            break;
                    }
                }
            });
        }
        if (params.facetOperators) {
            // Map operators to their respective parameters
            Object.entries(params.facetOperators).forEach(([group, operator]) => {
                switch (group) {
                    case 'pfam':
                        searchParams.set('pfam_operator', operator);
                        break;
                    case 'interpro':
                        searchParams.set('interpro_operator', operator);
                        break;
                    case 'cog_id':
                        searchParams.set('cog_id_operator', operator);
                        break;
                    case 'cog_funcats':
                        searchParams.set('cog_funcats_operator', operator);
                        break;
                    case 'kegg':
                        searchParams.set('kegg_operator', operator);
                        break;
                }
            });
        }

        const response = await ApiService.get<GeneFacetResponse>("/genes/faceted-search", searchParams);
        if (!response) {
            throw new Error('Failed to fetch facets');
        }

        return response;
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
    static async fetchEssentialityData(apiUrl: string, refName: string): Promise<Record<string, unknown>> {
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
     * Build parameters for fetching gene search results
     */
    static buildParamsFetchGeneSearchResults(
        query: string,
        page: number,
        pageSize: number,
        sortField: string,
        sortOrder: string,
        genomeFilter?: Array<{ isolate_name: string; type_strain: boolean }>,
        speciesFilter?: string[],
        selectedFacets?: Record<string, string[]>
    ): URLSearchParams {
        const params = new URLSearchParams({
            query,
            page: String(page),
            per_page: String(pageSize),
            sort_field: sortField,
            sort_order: sortOrder,
        });

        if (genomeFilter?.length) {
            params.append('isolates', genomeFilter.map(g => g.isolate_name).join(','));
        }

        if (speciesFilter?.length) {
            params.append('species', speciesFilter.join(','));
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

        return params;
    }

    /**
     * Fetch gene search results with advanced filtering
     */
    static async fetchGeneSearchResultsAdvanced(
        query: string,
        page: number,
        pageSize: number,
        sortField: string,
        sortOrder: string,
        genomeFilter?: Array<{ isolate_name: string; type_strain: boolean }>,
        speciesFilter?: string[],
        selectedFacets?: Record<string, string[]>,
        facetOperators?: Record<string, 'AND' | 'OR'>
    ): Promise<PaginatedResponse<GeneMeta>> {
        try {
            const params = this.buildParamsFetchGeneSearchResults(
                query,
                page,
                pageSize,
                sortField,
                sortOrder,
                genomeFilter,
                speciesFilter,
                selectedFacets
            );

            if (facetOperators) {
                params.append('facet_operators', JSON.stringify(facetOperators));
            }

            const response = await ApiService.get<PaginatedResponse<GeneMeta>>('genes/search/advanced', params);
            return response;
        } catch (error) {
            console.error('Error fetching gene search results:', error);
            throw error;
        }
    }

    /**
     * Fetch genes by search query
     */
    static async fetchGeneBySearch(
        isolate_name: string,
        searchQuery: string
    ): Promise<PaginatedResponse<GeneMeta>> {
        try {
            const params = new URLSearchParams({
                query: searchQuery,
                isolates: isolate_name
            });
            const response = await ApiService.get<PaginatedResponse<GeneMeta>>('genes/search', params);
            return response;
        } catch (error) {
            console.error('Error fetching genes by search:', error);
            throw error;
        }
    }
}
