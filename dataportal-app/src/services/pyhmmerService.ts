import { API_BASE_URL } from '../utils/common/constants';
import {
    PyhmmerDatabase,
    PyhmmerSearchRequest,
    PyhmmerSearchResponse,
    PyhmmerJobDetailsResponse,
    PyhmmerMXChoice,
    PyhmmerDomain
} from '../interfaces/Pyhmmer';
import { BaseService } from './common/BaseService';
import { cacheResponse } from './common/cachingDecorator';
import { ApiService } from './common/api';

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
            
            // Call API directly to handle validation errors properly
            const result = await ApiService.post<PyhmmerSearchResponse>(`${API_BASE_SEARCH}`, request);
            console.log('PyhmmerService.search: Successfully submitted search, received response:', result);
            return result;
        } catch (error) {
            console.error("Error performing Pyhmmer search:", error);
            
            // Enhanced error handling for validation errors
            if (error && typeof error === 'object' && 'response' in error) {
                const axiosError = error as any;
                if (axiosError.response?.status === 422) {
                    // This is a validation error - try to extract the actual message
                    const responseData = axiosError.response.data;
                    console.log('PyhmmerService.search: Validation error response:', responseData);
                    
                    if (responseData && typeof responseData === 'object') {
                        // Try to extract validation message from different possible formats
                        let validationMessage = '';
                        
                        if (responseData.detail && Array.isArray(responseData.detail)) {
                            // Pydantic validation error format
                            const messages = responseData.detail.map((err: any) => err.msg || err.message || err).filter(Boolean);
                            validationMessage = messages.join('; ');
                        } else if (responseData.message) {
                            validationMessage = responseData.message;
                        } else if (responseData.detail) {
                            validationMessage = responseData.detail;
                        } else if (responseData.error) {
                            validationMessage = responseData.error;
                        } else if (Array.isArray(responseData)) {
                            // Handle array of validation errors
                            validationMessage = responseData.map((err: any) => err.message || err.msg || err).join('; ');
                        }
                        
                        if (validationMessage) {
                            throw new Error(validationMessage);
                        }
                    }
                }
            }
            
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
            console.log(`PyhmmerService.getJobDetails: Task result length: ${Array.isArray(result.task?.result) ? result.task?.result.length : 'N/A'}`);
            return result;
        } catch (error) {
            console.error("Error fetching Pyhmmer job details:", error);
            throw new Error(`Failed to fetch job details: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    static async getDomainsByTarget(jobId: string, target: string): Promise<PyhmmerDomain[]> {
        try {
            console.log(`PyhmmerService.getDomainsByTarget: Fetching domains for job ${jobId}, target ${target}`);
            // Add cache-busting parameter to ensure fresh data
            const timestamp = Date.now();
            const result = await this.getWithRetry<any>(`${API_BASE_RESULT}/${jobId}/domains?target=${encodeURIComponent(target)}&_t=${timestamp}`);
            console.log(`PyhmmerService.getDomainsByTarget: Received response:`, result);
            
            // Debug: Log the specific domain data
            if (result && Array.isArray(result.domains)) {
                console.log('PyhmmerService.getDomainsByTarget: Domain identity:', result.domains[0]?.alignment_display?.identity);
                console.log('PyhmmerService.getDomainsByTarget: Domain similarity:', result.domains[0]?.alignment_display?.similarity);
                return result.domains;
            } else if (Array.isArray(result)) {
                console.log('PyhmmerService.getDomainsByTarget: Direct array result, domain identity:', result[0]?.alignment_display?.identity);
                return result;
            } else {
                throw new Error('Invalid domain response format');
            }
        } catch (error) {
            console.error("Error fetching Pyhmmer domains:", error);
            throw new Error(`Failed to fetch domains: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    static async downloadResults(jobId: string, format: 'tab' | 'fasta' | 'aligned_fasta'): Promise<Blob> {
        try {
            console.log(`PyhmmerService.downloadResults: Downloading results for job ${jobId} in format ${format}`);
            
            const url = `${API_BASE_URL}${API_BASE_RESULT}/${jobId}/download?format=${format}`;
            console.log(`PyhmmerService.downloadResults: Download URL: ${url}`);
            
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const blob = await response.blob();
            console.log(`PyhmmerService.downloadResults: Successfully downloaded ${blob.size} bytes`);
            return blob;
        } catch (error) {
            console.error("Error downloading Pyhmmer results:", error);
            throw new Error(`Failed to download results: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    // Remove a search from browser history
    static removeFromHistory(jobId: string): void {
        try {
            const historyKey = 'pyhmmer_search_history';
            const existingHistory = localStorage.getItem(historyKey);
            
            if (existingHistory) {
                const history = JSON.parse(existingHistory);
                const filteredHistory = history.filter((item: any) => item.jobId !== jobId);
                
                // Update localStorage
                localStorage.setItem(historyKey, JSON.stringify(filteredHistory));
                console.log(`PyhmmerService.removeFromHistory: Removed job ${jobId} from history`);
            }
        } catch (error) {
            console.error("Error removing item from history:", error);
        }
    }
}
