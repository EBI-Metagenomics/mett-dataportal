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
            return await this.getWithRetry<PyhmmerDatabase[]>(`${API_BASE_SEARCH}/databases`);
        } catch (error) {
            console.error("Error fetching Pyhmmer databases:", error);
            throw error;
        }
    }

    @cacheResponse(60 * 60 * 1000, () => "getMXChoices")
    static async getMXChoices(): Promise<PyhmmerMXChoice[]> {
        try {
            return await this.getWithRetry<PyhmmerMXChoice[]>(`${API_BASE_SEARCH}/mxchoices`);
        } catch (error) {
            console.error("Error fetching Pyhmmer MX choices:", error);
            throw error;
        }
    }

    static async search(request: PyhmmerSearchRequest): Promise<PyhmmerSearchResponse> {
        try {
            return await this.postWithRetry<PyhmmerSearchResponse>(`${API_BASE_SEARCH}`, request);
        } catch (error) {
            console.error("Error performing Pyhmmer search:", error);
            throw error;
        }
    }

    static async getJobDetails(id: string): Promise<PyhmmerJobDetailsResponse> {
        try {
            return await this.getWithRetry<PyhmmerJobDetailsResponse>(`${API_BASE_RESULT}/${id}`);
        } catch (error) {
            console.error(`Error fetching Pyhmmer job details for ID ${id}:`, error);
            throw error;
        }
    }
}
