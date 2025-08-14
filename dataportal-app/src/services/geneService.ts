import { BaseService } from "./common/BaseService";
import { Gene, GeneFacetResponse, GeneMeta, GeneProteinSeq, GeneSuggestion } from "../interfaces/Gene";
import { PaginatedApiResponse } from "../interfaces/ApiResponse";
import { cacheResponse } from "./common/cachingDecorator";
import { DEFAULT_PER_PAGE_CNT, API_BASE_URL } from "../utils/common/constants";

export class GeneService extends BaseService {
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
            const params = this.buildParams({
                query,
                limit,
                species_acronym: speciesAcronym,
                isolates: genomeIds
            });

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

            return await this.getWithRetry<GeneSuggestion[]>("genes/autocomplete", params);
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
        facetOperators?: Record<string, 'AND' | 'OR'>,
        locusTag?: string
    ): Promise<PaginatedApiResponse<GeneMeta>> {
        try {
            console.log('GeneService.fetchGeneSearchResultsAdvanced called with:', {
                query, page, perPage, sortField, sortOrder, selectedGenomes, selectedSpecies, selectedFacets, facetOperators, locusTag
            });
            
            // Use the same parameter construction logic as buildParamsFetchGeneSearchResults
            const params = this.buildParamsFetchGeneSearchResults(
                query,
                page,
                perPage,
                sortField,
                sortOrder,
                selectedGenomes,
                selectedSpecies,
                selectedFacets,
                facetOperators,
                locusTag
            );

            const response = await BaseService.getRawResponse<GeneMeta[]>("/genes/search/advanced", params);
            // console.log('GeneService.fetchGeneSearchResultsAdvanced - URL params:', params.toString());
            // console.log('GeneService.fetchGeneSearchResultsAdvanced response:', response);
            return response as PaginatedApiResponse<GeneMeta>;
        } catch (error) {
            console.error("Error fetching gene search results:", error);
            throw error;
        }
    }

    /**
     * Fetch gene search results by genome ID.
     */
    static async fetchGeneBySearch(
        genomeId: string,
        query: string,
        page: number = 1
    ): Promise<PaginatedApiResponse<Gene>> {
        try {
            const params = this.buildParams({ query, page });
            const url = genomeId ? `species/${genomeId}/genomes/search` : "";
            return await this.getWithRetry<PaginatedApiResponse<Gene>>(url, params);
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
    ): Promise<PaginatedApiResponse<GeneMeta>> {
        try {
            const params = this.buildParams({ page, per_page: perPage });
            return await this.getWithRetry<PaginatedApiResponse<GeneMeta>>(`genomes/${isolate_name}/genes`, params);
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
            return await this.getWithRetry<GeneMeta>(`/genes/${locus_tag}`);
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
            return await this.getWithRetry<GeneProteinSeq>(`/genes/protein/${locus_tag}`);
        } catch (error) {
            console.error(`Error fetching protein sequence for locus tag ${locus_tag}:`, error);
            throw error;
        }
    }

    @cacheResponse(60 * 60 * 1000, (apiUrl: string, refName: string) => `${apiUrl}:${refName}`) // Cache for 60 minutes, uses combined key
    static async fetchEssentialityData(apiUrl: string, refName: string): Promise<Record<string, any>> {
        try {
            console.log(`Fetching essentiality data from: ${apiUrl}/${refName}`);
            const response = await fetch(`${apiUrl}/${refName}`);
            if (!response.ok) {
                console.warn(`Failed to fetch essentiality data for ${refName}: ${response.status} ${response.statusText}`);
                return {};
            }
            const data = await response.json();
            console.log(`Essentiality data received for ${refName}:`, data);
            return data;
        } catch (error) {
            console.error(`Error fetching essentiality data for ${refName}:`, error);
            return {};
        }
    }

    /**
     * Fetch gene facets for filtering.
     */
    static async fetchGeneFacets(
        query?: string,
        speciesAcronym?: string,
        isolates?: string,
        essentiality?: string,
        cogId?: string,
        cogFuncats?: string,
        kegg?: string,
        goTerm?: string,
        pfam?: string,
        interpro?: string,
        hasAmrInfo?: string,
        facetOperators?: Record<string, 'AND' | 'OR'>
    ): Promise<GeneFacetResponse> {
        try {
            // console.log('GeneService.fetchGeneFacets called with:', {
            //     query, speciesAcronym, isolates, essentiality, cogId, cogFuncats,
            //     kegg, goTerm, pfam, interpro, hasAmrInfo, facetOperators
            // });

            const params = this.buildParams({
                query,
                species_acronym: speciesAcronym,
                isolates,
                essentiality,
                cog_id: cogId,
                cog_funcats: cogFuncats,
                kegg,
                go_term: goTerm,
                pfam,
                interpro,
                has_amr_info: hasAmrInfo
            });

            // Add facet operators as individual parameters
            if (facetOperators) {
                if (facetOperators.pfam) params.append('pfam_operator', facetOperators.pfam);
                if (facetOperators.interpro) params.append('interpro_operator', facetOperators.interpro);
                if (facetOperators.cog_id) params.append('cog_id_operator', facetOperators.cog_id);
                if (facetOperators.cog_funcats) params.append('cog_funcats_operator', facetOperators.cog_funcats);
                if (facetOperators.kegg) params.append('kegg_operator', facetOperators.kegg);
                if (facetOperators.go_term) params.append('go_term_operator', facetOperators.go_term);
            }

            // console.log('Making API call to genes/faceted-search with params:', params.toString());
            const response = await this.getWithRetry<GeneFacetResponse>('genes/faceted-search', params);
            // console.log('API response received:', response);
            return response;
        } catch (error) {
            console.error('Error fetching gene facets:', error);
            throw error;
        }
    }

    /**
     * Download gene data in TSV format.
     */
    static async downloadGenesTSV(
        query: string,
        sortField: string,
        sortOrder: string,
        selectedGenomes?: { isolate_name: string; type_strain: boolean }[],
        selectedSpecies?: string[],
        selectedFacets?: Record<string, string[]>,
        facetOperators?: Record<string, 'AND' | 'OR'>
    ): Promise<void> {
        try {
            const params = this.buildParams({
                query,
                page: 1,
                per_page: 1000000,
                sort_field: sortField,
                sort_order: sortOrder,
                isolates: selectedGenomes?.map(g => g.isolate_name).join(","),
                species_acronym: selectedSpecies?.length === 1 ? selectedSpecies[0] : undefined
            });

            // Add filters and operators
            if (selectedFacets) {
                const filterParts: string[] = [];
                for (const [key, rawValue] of Object.entries(selectedFacets)) {
                    let values: string[] = [];
                    if (Array.isArray(rawValue)) {
                        values = rawValue.map(String);
                    } else if (rawValue !== undefined && rawValue !== null) {
                        values = [String(rawValue)];
                    }
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
                for (const [key, value] of Object.entries(facetOperators)) {
                    if (value) {
                        filterOpParts.push(`${key}:${value}`);
                    }
                }
                if (filterOpParts.length > 0) {
                    params.append("filter_operators", filterOpParts.join(";"));
                }
            }

            const url = this.createDownloadUrl(`${API_BASE_URL}/genes/download/tsv`, params);
            this.triggerDownload(url, 'genes_export.tsv');
        } catch (error) {
            console.error('Error downloading genes TSV:', error);
            throw error;
        }
    }

    // Legacy methods for backward compatibility
    static buildParamsFetchGeneSearchResults(
        query: string,
        page: number,
        perPage: number,
        sortField: string,
        sortOrder: string,
        selectedGenomes?: { isolate_name: string; type_strain: boolean }[],
        selectedSpecies?: string[],
        selectedFacets?: Record<string, string[]>,
        facetOperators?: Record<string, 'AND' | 'OR'>,
        locusTag?: string
    ): URLSearchParams {
        const params = this.buildParams({
            query,
            page,
            per_page: perPage,
            sort_field: sortField,
            sort_order: sortOrder,
            isolates: selectedGenomes?.map(g => g.isolate_name).join(","),
            species_acronym: selectedSpecies?.length === 1 ? selectedSpecies[0] : undefined
        });

        // Add locus_tag parameter if provided (takes precedence over query)
        if (locusTag) {
            params.append("locus_tag", locusTag);
        }

        if (selectedFacets) {
            const filterParts: string[] = [];
            for (const [key, rawValue] of Object.entries(selectedFacets)) {
                let values: string[] = [];
                if (Array.isArray(rawValue)) {
                    values = rawValue.map(String);
                } else if (rawValue !== undefined && rawValue !== null) {
                    values = [String(rawValue)];
                }
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
            for (const [key, value] of Object.entries(facetOperators)) {
                if (value) {
                    filterOpParts.push(`${key}:${value}`);
                }
            }
            if (filterOpParts.length > 0) {
                params.append("filter_operators", filterOpParts.join(";"));
            }
        }

        return params;
    }
}
