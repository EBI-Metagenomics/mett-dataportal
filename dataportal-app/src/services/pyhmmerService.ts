import {
    PyhmmerDatabase,
    PyhmmerSearchRequest,
    PyhmmerSearchResponse,
    PyhmmerJobDetailsResponse,
    PyhmmerMXChoice
} from '../interfaces/Pyhmmer';
import { ApiService } from './api';
import { cacheResponse } from './cachingDecorator';

const API_BASE_SEARCH = '/pyhmmer/search';
const API_BASE_RESULT = '/pyhmmer/result';

export class PyhmmerService {
    @cacheResponse(60 * 60 * 1000, () => "getDatabases")
    static async getDatabases(): Promise<PyhmmerDatabase[]> {
        return await ApiService.get(`${API_BASE_SEARCH}/databases`);
    }

    @cacheResponse(60 * 60 * 1000, () => "getMXChoices")
    static async getMXChoices(): Promise<PyhmmerMXChoice[]> {
        return await ApiService.get(`${API_BASE_SEARCH}/mxchoices`);
    }


    static async search(request: PyhmmerSearchRequest): Promise<PyhmmerSearchResponse> {
        return await ApiService.post(`${API_BASE_SEARCH}`, request);
    }

    static async getJobDetails(id: string): Promise<PyhmmerJobDetailsResponse> {
        return await ApiService.get(`${API_BASE_RESULT}/${id}`);
    }
}
