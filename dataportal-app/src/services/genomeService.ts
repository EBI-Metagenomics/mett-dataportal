import {ApiService} from "./api";
import {AutocompleteResponse, GenomeMeta, GenomeResponse} from "../interfaces/Genome";
import {transformAutocompleteResponse, transformGenomeMeta, transformGenomeResponse} from "../utils/transformer";
import {DEFAULT_PER_PAGE_CNT, API_BASE_URL} from "../utils/appConstants";

export class GenomeService {
    /**
     * Fetch genome autocomplete suggestions.
     */
    static async fetchGenomeAutocompleteSuggestions(
        inputQuery: string,
        selectedSpecies?: string
    ): Promise<AutocompleteResponse[]> {
        try {
            const params = new URLSearchParams({
                query: inputQuery,
                // ...(selectedSpecies && {species_acronym: selectedSpecies}),
                ...(selectedSpecies && selectedSpecies.length === 1 && {species_acronym: selectedSpecies}),
            });

            const rawResponse = await ApiService.get("/genomes/autocomplete", params);
            // console.log("response: ", rawResponse);

            // Transform raw response to match AutocompleteResponse
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
            const params = new URLSearchParams({isolates: isolateNames.join(",")});
            const rawResponse = await ApiService.get("/genomes/by-isolate-names", params);
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
    ): Promise<GenomeResponse> {
        try {
            const params = new URLSearchParams({
                query,
                page: String(page),
                per_page: String(pageSize),
                sortField,
                sortOrder,

            });

            if (typeStrainFilter && typeStrainFilter.length) {
                params.append('isolates', typeStrainFilter.join(','));
            }

            const endpoint = (selectedSpecies && selectedSpecies.length === 1)
                ? `/species/${selectedSpecies[0]}/genomes/search`
                : `/genomes/search`;

            const rawResponse = await ApiService.get(endpoint, params);
            return transformGenomeResponse(rawResponse);
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
    ): Promise<GenomeResponse> {
        try {
            const baseUrl = species.length === 1 ? `species/${species[0]}/genomes/search` : `genomes/search`;

            const params = new URLSearchParams({
                query: genome,
                sortField,
                sortOrder,
            });

            const rawResponse = await ApiService.get(baseUrl, params);
            return transformGenomeResponse(rawResponse);
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
            const rawResponse = await ApiService.get("/genomes/type-strains");
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
            const params = new URLSearchParams({
                query,
                sortField,
                sortOrder,
            });

            if (selectedTypeStrains && selectedTypeStrains.length) {
                params.append('isolates', selectedTypeStrains.join(','));
            }

            if (selectedSpecies && selectedSpecies.length === 1) {
                params.append('species_acronym', selectedSpecies[0]);
            }
            
            // Create download URL
            const url = `${API_BASE_URL}/genomes/download/tsv?${params.toString()}`;
            
            // Trigger download
            const link = document.createElement('a');
            link.href = url;
            link.download = 'genomes_export.tsv';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } catch (error) {
            console.error('Error downloading genomes TSV:', error);
            throw error;
        }
    }
}