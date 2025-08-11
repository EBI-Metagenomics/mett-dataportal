import { BaseService } from "./BaseService";
import { AutocompleteResponse, GenomeMeta } from "../interfaces/Genome";
import { PaginatedApiResponse } from "../interfaces/ApiResponse";
import { transformAutocompleteResponse, transformGenomeMeta } from "../utils/transformer";
import { DEFAULT_PER_PAGE_CNT, API_BASE_URL } from "../utils/constants";

// Valid sort fields for genomes
const VALID_GENOME_SORT_FIELDS = {
    'species': 'species',
    'isolate_name': 'isolate_name',
    'genome': 'isolate_name', // Map 'genome' to 'isolate_name'
    'strain': 'isolate_name', // Map 'strain' to 'isolate_name'
    'name': 'isolate_name', // Map 'name' to 'isolate_name'
};

/**
 * Map sort field to valid backend field
 */
const mapSortField = (field: string): string => {
    return VALID_GENOME_SORT_FIELDS[field as keyof typeof VALID_GENOME_SORT_FIELDS] || 'isolate_name';
};

export class GenomeService extends BaseService {
    /**
     * Fetch genome autocomplete suggestions.
     */
    static async fetchGenomeAutocompleteSuggestions(
        inputQuery: string,
        selectedSpecies?: string
    ): Promise<AutocompleteResponse[]> {
        try {
            const params = this.buildParams({
                query: inputQuery,
                species_acronym: selectedSpecies && selectedSpecies.length === 1 ? selectedSpecies : undefined
            });

            const rawResponse = await this.getWithRetry<AutocompleteResponse[]>("/genomes/autocomplete", params);
            return transformAutocompleteResponse(rawResponse);
        } catch (error) {
            console.error("Error fetching genome suggestions:", error);
            throw error;
        }
    }

    /**
     * Fetch genomes by isolate names.
     */
    static async fetchGenomeByIsolateNames(isolateNames: string[]): Promise<GenomeMeta[]> {
        try {
            const params = this.buildParams({ isolates: isolateNames.join(",") });
            const rawResponse = await this.getWithRetry<GenomeMeta[]>("/genomes/by-isolate-names", params);
            return rawResponse.map(transformGenomeMeta);
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
        selectedSpecies?: string[],
        typeStrainFilter?: string[],
    ): Promise<PaginatedApiResponse<GenomeMeta>> {
        try {
            console.log('GenomeService.fetchGenomeSearchResults called with:', {
                query, page, pageSize, sortField, sortOrder, selectedSpecies, typeStrainFilter
            });
            
            // Map sort field to valid backend field
            const mappedSortField = mapSortField(sortField);
            console.log(`Mapping sort field from '${sortField}' to '${mappedSortField}'`);
            
            const params = this.buildParams({
                query,
                page,
                per_page: pageSize,
                sortField: mappedSortField,
                sortOrder,
                isolates: typeStrainFilter?.join(',')
            });

            const endpoint = (selectedSpecies && selectedSpecies.length === 1)
                ? `/species/${selectedSpecies[0]}/genomes/search`
                : `/genomes/search`;

            const response = await BaseService.getRawResponse<GenomeMeta[]>(endpoint, params);
            console.log('GenomeService.fetchGenomeSearchResults response:', response);
            return response as PaginatedApiResponse<GenomeMeta>;
        } catch (error) {
            console.error("Error fetching genome search results:", error);
            throw error;
        }
    }

    /**
     * Fetch genomes by search query and species filter.
     */
    static async fetchGenomesBySearch(
        species: string[],
        genome: string,
        sortField: string,
        sortOrder: string
    ): Promise<PaginatedApiResponse<GenomeMeta>> {
        try {
            const baseUrl = species.length === 1 ? `species/${species[0]}/genomes/search` : `genomes/search`;

            // Map sort field to valid backend field
            const mappedSortField = mapSortField(sortField);
            console.log(`Mapping sort field from '${sortField}' to '${mappedSortField}'`);

            const params = this.buildParams({
                query: genome,
                sortField: mappedSortField,
                sortOrder,
            });

            const response = await BaseService.getRawResponse<GenomeMeta[]>(baseUrl, params);
            console.log('GenomeService.fetchGenomesBySearch response:', response);
            return response as PaginatedApiResponse<GenomeMeta>;
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
     * Fetch all type strains.
     */
    static async fetchTypeStrains(): Promise<GenomeMeta[]> {
        try {
            const rawResponse = await this.getWithRetry<GenomeMeta[]>("/genomes/type-strains");
            return rawResponse.map(transformGenomeMeta);
        } catch (error) {
            console.error("Error fetching type strains:", error);
            throw error;
        }
    }

    /**
     * Download genome data in TSV format.
     */
    static async downloadGenomesTSV(
        query: string,
        sortField: string,
        sortOrder: string,
        selectedSpecies: string[],
        selectedTypeStrains: string[]
    ): Promise<void> {
        try {
            // Map sort field to valid backend field
            const mappedSortField = mapSortField(sortField);
            
            const params = this.buildParams({
                query,
                sortField: mappedSortField,
                sortOrder,
                isolates: selectedTypeStrains?.join(','),
                species_acronym: selectedSpecies?.length === 1 ? selectedSpecies[0] : undefined
            });

            const url = this.createDownloadUrl(`${API_BASE_URL}/genomes/download/tsv`, params);
            this.triggerDownload(url, 'genomes_export.tsv');
        } catch (error) {
            console.error('Error downloading genomes TSV:', error);
            throw error;
        }
    }
}