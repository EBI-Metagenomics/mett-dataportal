import {API_BASE_URL} from '../../utils/common';
import {PYHMMER_CONSTANTS} from '../../utils/pyhmmer';
import {
    PyhmmerDatabase,
    PyhmmerDomain,
    PyhmmerJobDetailsResponse,
    PyhmmerMXChoice,
    PyhmmerSearchRequest,
    PyhmmerSearchResponse
} from '../../interfaces/Pyhmmer';
import {ApiService, BaseService, cacheResponse} from '../common';

const API_BASE_SEARCH = '/pyhmmer/search';
const API_BASE_RESULT = '/pyhmmer/result';

// Unified PyHMMER Search Result interface
export interface PyhmmerSearchResult {
    target_name: string;
    evalue: string | number;
    score: string | number;
    is_significant?: boolean;
    significant?: boolean;
    significant_match?: boolean;
    significantMatch?: boolean;
    description?: string;
    sequence?: string;
}

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

    // NEW: Unified search execution method (replaces PyhmmerSearchService)
    static async executeSearch(proteinSequence: string, database: string = PYHMMER_CONSTANTS.DATABASES.DEFAULT): Promise<{results: PyhmmerSearchResult[], jobId: string}> {
        try {
            // Convert to FASTA format
            const fastaSequence = `>protein\n${proteinSequence}`;

            const searchRequest: PyhmmerSearchRequest = {
                database: database,
                threshold: 'evalue',
                threshold_value: PYHMMER_CONSTANTS.THRESHOLDS.DEFAULT_EVALUE,
                input: fastaSequence,
                E: PYHMMER_CONSTANTS.THRESHOLDS.DEFAULT_EVALUE,
                domE: PYHMMER_CONSTANTS.THRESHOLDS.DEFAULT_DOM_EVALUE,
                incE: PYHMMER_CONSTANTS.THRESHOLDS.DEFAULT_INC_EVALUE,
                incdomE: PYHMMER_CONSTANTS.THRESHOLDS.DEFAULT_INCDOM_EVALUE
            };

            const response = await this.search(searchRequest);

            if (response.id) {
                // Poll for results
                const results = await this.pollJobStatus(response.id);
                return { results, jobId: response.id };
            } else {
                throw new Error('Failed to submit search');
            }
        } catch (error: any) {
            console.error('PyHMMER search error:', error);
            throw error;
        }
    }

    // NEW: Poll job status until completion (moved from PyhmmerSearchService)
    private static async pollJobStatus(jobId: string): Promise<PyhmmerSearchResult[]> {
        const maxAttempts = PYHMMER_CONSTANTS.TIMING.MAX_JOB_POLL_ATTEMPTS;
        let attempts = 0;

        while (attempts < maxAttempts) {
            try {
                const jobDetails = await this.getJobDetails(jobId);
                console.log('PyhmmerService.pollJobStatus: Full jobDetails:', jobDetails);
                
                const status = jobDetails.status;
                console.log('PyhmmerService.pollJobStatus: Job status:', status);

                // Check for completed status (handle both lowercase and uppercase)
                const normalizedStatus = status?.toUpperCase();
                if (normalizedStatus === 'COMPLETED' || normalizedStatus === 'SUCCESS') {
                    const results = jobDetails.task?.result || [];
                    console.log('PyhmmerService.pollJobStatus: Results type:', typeof results);
                    console.log('PyhmmerService.pollJobStatus: Results is array:', Array.isArray(results));
                    console.log('PyhmmerService.pollJobStatus: Results length:', Array.isArray(results) ? results.length : 'N/A');

                    // Handle different result formats
                    if (Array.isArray(results)) {
                        // Convert unknown results to PyhmmerSearchResult
                        const convertedResults = results.map(result => this.convertToSearchResult(result));
                        console.log('PyhmmerService.pollJobStatus: Converted results count:', convertedResults.length);
                        return convertedResults;
                    } else if (results && typeof results === 'object') {
                        // If results is an object, try to extract the array
                        const resultKeys = Object.keys(results);
                        console.log('PyhmmerService.pollJobStatus: Result object keys:', resultKeys);

                        // Look for common result array keys
                        for (const key of ['hits', 'domains', 'results', 'data']) {
                            if (Array.isArray(results[key])) {
                                console.log(`PyhmmerService.pollJobStatus: Found array in key '${key}' with ${results[key].length} items`);
                                return (results[key] as unknown[]).map(result => this.convertToSearchResult(result));
                            }
                        }

                        // If no array found, return the object as a single result
                        console.log('PyhmmerService.pollJobStatus: No array found, converting object as single result');
                        return [this.convertToSearchResult(results)];
                    } else {
                        console.warn('PyhmmerService.pollJobStatus: Results is not an array or object, returning empty array');
                        return [];
                    }
                } else if (normalizedStatus === 'FAILED' || normalizedStatus === 'FAILURE') {
                    throw new Error('PyHMMER search failed');
                }

                // Job still processing, wait and retry
                console.log(`PyhmmerService.pollJobStatus: Job status is '${status}', waiting before retry (attempt ${attempts + 1}/${maxAttempts})`);
                await new Promise(resolve => setTimeout(resolve, PYHMMER_CONSTANTS.TIMING.JOB_POLL_INTERVAL));
                attempts++;
            } catch (error) {
                console.error('PyhmmerService.pollJobStatus: Error polling job status:', error);
                throw error;
            }
        }
        throw new Error('PyHMMER search timed out');
    }

    // Helper method to convert unknown results to PyhmmerSearchResult
    private static convertToSearchResult(result: unknown): PyhmmerSearchResult {
        if (result && typeof result === 'object') {
            const resultObj = result as Record<string, unknown>;
            
            // Extract target name (backend uses 'target', frontend expects 'target_name')
            const targetName = resultObj.target_name || resultObj.name || resultObj.target || 'Unknown';
            
            // Extract evalue (backend returns as string, convert to number if needed)
            let evalue: string | number = 0;
            if (resultObj.evalue !== undefined && resultObj.evalue !== null) {
                if (typeof resultObj.evalue === 'string') {
                    evalue = resultObj.evalue;
                } else {
                    evalue = Number(resultObj.evalue) || 0;
                }
            }
            
            // Extract score (backend returns as string, convert to number if needed)
            let score: string | number = 0;
            if (resultObj.score !== undefined && resultObj.score !== null) {
                if (typeof resultObj.score === 'string') {
                    score = resultObj.score;
                } else {
                    score = Number(resultObj.score) || 0;
                }
            }
            
            // Extract is_significant (handle various field names)
            const isSignificant = Boolean(
                resultObj.is_significant !== undefined ? resultObj.is_significant :
                resultObj.significant !== undefined ? resultObj.significant :
                resultObj.significant_match !== undefined ? resultObj.significant_match :
                resultObj.significantMatch !== undefined ? resultObj.significantMatch :
                false
            );
            
            return {
                target_name: String(targetName),
                evalue: evalue,
                score: score,
                is_significant: isSignificant,
                description: resultObj.description ? String(resultObj.description) : undefined,
                sequence: resultObj.sequence ? String(resultObj.sequence) : undefined
            };
        }

        // Fallback for unexpected result types
        console.warn('PyhmmerService.convertToSearchResult: Unexpected result type:', typeof result, result);
        return {
            target_name: 'Unknown',
            evalue: 0,
            score: 0,
            is_significant: false
        };
    }

    // Utility methods for formatting and validation
    static formatEvalue(evalueRaw: string | number): string {
        const evalue = typeof evalueRaw === 'string' ? parseFloat(evalueRaw) : Number(evalueRaw);

        if (!isNaN(evalue) && isFinite(evalue)) {
            if (evalue < 0.01) {
                return evalue.toExponential(2);
            } else {
                return evalue.toFixed(6);
            }
        } else {
            return String(evalueRaw);
        }
    }

    static formatScore(scoreRaw: string | number): string {
        const score = typeof scoreRaw === 'string' ? parseFloat(scoreRaw) : Number(scoreRaw);

        if (!isNaN(score) && isFinite(score)) {
            return score.toFixed(1);
        } else {
            return String(scoreRaw);
        }
    }

    static isResultSignificant(result: PyhmmerSearchResult): boolean {
        const isSignificant = result.is_significant || result.significant || result.significant_match || result.significantMatch;
        return isSignificant === true;
    }

    static getTargetName(result: PyhmmerSearchResult): string {
        return result.target_name || 'Unknown';
    }

    static generateGenomeViewerUrl(targetName: string): string {
        const strainPrefix = targetName.substring(0, targetName.lastIndexOf('_'));
        return `/genome/${strainPrefix}?locus_tag=${encodeURIComponent(targetName)}`;
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
