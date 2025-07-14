import { BaseService } from "./BaseService";
import { PaginatedResponse, Species } from "../interfaces/Species";

export class SpeciesService extends BaseService {
    /**
     * Fetch all species data.
     */
    static async fetchSpeciesList(): Promise<Species[]> {
        try {
            const response = await this.getWithRetry<Species[]>("species/");
            if (Array.isArray(response)) {
                return response.map((item: any) => ({
                    scientific_name: item.scientific_name || item.name,
                    common_name: item.common_name || item.name,
                    acronym: item.acronym || item.name,
                    taxonomy_id: item.taxonomy_id
                }));
            } else {
                console.error("Invalid response format for species list:", response);
                return [];
            }
        } catch (error) {
            console.error("Error fetching species list:", error);
            throw error;
        }
    }

    /**
     * Fetch isolate list with optional species ID.
     */
    static async fetchIsolateList(speciesId?: string): Promise<PaginatedResponse<Species>> {
        try {
            const params = this.buildParams({ species: speciesId });
            const response = await this.getWithRetry<PaginatedResponse<Species>>("/api/isolates", params);
            if (response && response.data) {
                return response;
            } else {
                console.error("Invalid response format for isolate list:", response);
                return { data: [], total: 0 };
            }
        } catch (error) {
            console.error("Error fetching isolates:", { speciesId, error });
            throw error;
        }
    }
}
