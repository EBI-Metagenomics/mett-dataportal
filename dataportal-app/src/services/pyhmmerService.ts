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
            
            // Enhanced logging for all parameters
            console.log('=== FRONTEND SEARCH PARAMETERS ===');
            console.log('Database:', request.database);
            console.log('Threshold type:', request.threshold);
            console.log('Threshold value:', request.threshold_value);
            console.log('Substitution matrix (mx):', request.mx);
            console.log('Input sequence length:', request.input?.length || 0);
            
            // E-value parameters
            console.log('=== E-VALUE PARAMETERS ===');
            console.log('E (Report E-values - Sequence):', request.E);
            console.log('domE (Report E-values - Hit):', request.domE);
            console.log('incE (Significance E-values - Sequence):', request.incE);
            console.log('incdomE (Significance E-values - Hit):', request.incdomE);
            
            // Bit score parameters
            console.log('=== BIT SCORE PARAMETERS ===');
            console.log('T (Report Bit scores - Sequence):', request.T);
            console.log('domT (Report Bit scores - Hit):', request.domT);
            console.log('incT (Significance Bit scores - Sequence):', request.incT);
            console.log('incdomT (Significance Bit scores - Hit):', request.incdomT);
            
            // Gap penalties
            console.log('=== GAP PENALTIES ===');
            console.log('popen (Gap open penalty):', request.popen);
            console.log('pextend (Gap extend penalty):', request.pextend);
            
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
