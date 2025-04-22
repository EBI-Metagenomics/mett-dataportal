import {ApiService} from "./api";
import {cacheResponse} from "./cachingDecorator";

export class MetadataService {
    /**
     * Fetch COG categories with in-memory cache for 1 hour.
     * Falls back to live API call if cache is expired.
     */
    @cacheResponse(60 * 60 * 1000) // 1 hour in milliseconds
    static async fetchCOGCategories(): Promise<{ code: string, label: string }[]> {
        const response = await ApiService.get("/metadata/cog-categories");
        if (Array.isArray(response)) {
            return response;
        } else {
            console.error("Invalid COG category response format:", response);
            return [];
        }
    }
}