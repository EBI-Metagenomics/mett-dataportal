import { BaseService } from "./BaseService";
import { cacheResponse } from "./cachingDecorator";

export class MetadataService extends BaseService {
    /**
     * Fetch COG categories with in-memory cache for 1 hour.
     * Falls back to live API call if cache is expired.
     */
    @cacheResponse(60 * 60 * 1000) // 1 hour in milliseconds
    static async fetchCOGCategories(): Promise<{ code: string, label: string }[]> {
        try {
            const response = await this.getWithRetry<{ code: string, label: string }[]>("/metadata/cog-categories");
            if (Array.isArray(response)) {
                return response;
            } else {
                console.error("Invalid COG category response format:", response);
                return [];
            }
        } catch (error) {
            console.error("Error fetching COG categories:", error);
            throw error;
        }
    }
}