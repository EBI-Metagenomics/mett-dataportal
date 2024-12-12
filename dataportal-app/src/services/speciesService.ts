import {ApiService} from "./api";
import {PaginatedResponse, Species} from "../interfaces/Species";

export class SpeciesService {
    /**
     * Fetch all species data.
     */
    static async fetchSpeciesList(): Promise<Species[]> {
        try {
            const response = await ApiService.get("species/");
            if (Array.isArray(response)) {
                return response.map((item: any) => ({
                    id: item.id,
                    scientific_name: item.scientific_name || item.name,
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
            const params = new URLSearchParams();
            if (speciesId) {
                params.append("species", speciesId);
            }

            const response = await ApiService.get("/api/isolates", params);
            if (response && response.data) {
                return response;
            } else {
                console.error("Invalid response format for isolate list:", response);
                return {data: [], total: 0};
            }
        } catch (error) {
            console.error("Error fetching isolates:", {speciesId, error});
            throw error;
        }
    }
}
