import {
    PyhmmerDatabase,
    PyhmmerSearchRequest,
    PyhmmerSearchResponse,
    PyhmmerJobDetailsResponse,
    PyhmmerMXChoice
} from '../interfaces/Pyhmmer';
import { BaseService } from './BaseService';
import { cacheResponse } from './cachingDecorator';

const API_BASE_SEARCH = '/pyhmmer/search';
const API_BASE_RESULT = '/pyhmmer/result';

export class PyhmmerService extends BaseService {
    @cacheResponse(60 * 60 * 1000, () => "getDatabases")
    static async getDatabases(): Promise<PyhmmerDatabase[]> {
        try {
            console.log('PyhmmerService.getDatabases: Attempting to fetch databases from:', `${API_BASE_SEARCH}/databases`);
            const result = await this.getWithRetry<PyhmmerDatabase[]>(`${API_BASE_SEARCH}/databases`);
            console.log('PyhmmerService.getDatabases: Successfully fetched databases:', result);
            return result;
        } catch (error) {
            console.error("Error fetching Pyhmmer databases:", error);
            // Return empty array instead of throwing to prevent UI crashes
            return [];
        }
    }

    @cacheResponse(60 * 60 * 1000, () => "getMXChoices")
    static async getMXChoices(): Promise<PyhmmerMXChoice[]> {
        try {
            console.log('PyhmmerService.getMXChoices: Attempting to fetch MX choices from:', `${API_BASE_SEARCH}/mx-choices`);
            const result = await this.getWithRetry<PyhmmerMXChoice[]>(`${API_BASE_SEARCH}/mx-choices`);
            console.log('PyhmmerService.getMXChoices: Successfully fetched MX choices:', result);
            return result;
        } catch (error) {
            console.error("Error fetching Pyhmmer MX choices:", error);
            // Return empty array instead of throwing to prevent UI crashes
            return [];
        }
    }

    static async search(request: PyhmmerSearchRequest): Promise<PyhmmerSearchResponse> {
        try {
            console.log('PyhmmerService.search: Attempting to submit search request to:', API_BASE_SEARCH);
            console.log('PyhmmerService.search: Request payload:', request);
            const result = await this.postWithRetry<PyhmmerSearchResponse>(`${API_BASE_SEARCH}`, request);
            console.log('PyhmmerService.search: Successfully submitted search, received response:', result);
            return result;
        } catch (error) {
            console.error("Error performing Pyhmmer search:", error);
            throw new Error(`Failed to submit Pyhmmer search: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    static async getJobDetails(jobId: string): Promise<PyhmmerJobDetailsResponse> {
        try {
            console.log(`PyhmmerService.getJobDetails: Fetching job details for ID: ${jobId}`);
            const result = await this.getWithRetry<PyhmmerJobDetailsResponse>(`${API_BASE_RESULT}/${jobId}`);
            console.log(`PyhmmerService.getJobDetails: Received response:`, result);
            console.log(`PyhmmerService.getJobDetails: Response status: ${result.status}`);
            console.log(`PyhmmerService.getJobDetails: Task status: ${result.task?.status}`);
            console.log(`PyhmmerService.getJobDetails: Task result type: ${typeof result.task?.result}`);
            console.log(`PyhmmerService.getJobDetails: Task result length: ${Array.isArray(result.task?.result) ? result.task.result.length : 'N/A'}`);
            return result;
        } catch (error) {
            console.error("Error fetching Pyhmmer job details:", error);
            throw new Error(`Failed to fetch job details: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }
}
