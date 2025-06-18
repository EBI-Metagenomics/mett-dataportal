import {
    PyhmmerDatabase,
    PyhmmerSearchRequest,
    PyhmmerSearchResponse,
    PyhmmerJobDetailsResponse
} from '../interfaces/Pyhmmer';
import { ApiService } from './api';

const API_BASE = '/pyhmmer';

export class PyhmmerService {
    static async getDatabases(): Promise<PyhmmerDatabase[]> {
        return await ApiService.get(`${API_BASE}/databases`);
    }

    static async search(request: PyhmmerSearchRequest): Promise<PyhmmerSearchResponse> {
        return await ApiService.post(`${API_BASE}/search`, request);
    }

    static async getJobDetails(id: string): Promise<PyhmmerJobDetailsResponse> {
        return await ApiService.get(`${API_BASE}/search/${id}`);
    }
}
