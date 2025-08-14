import { PyhmmerService } from '../pyhmmerService';

export interface PyhmmerSearchRequest {
    database: string;
    threshold: 'evalue';
    threshold_value: number;
    input: string;
    E: number;
    domE: number;
    incE: number;
    incdomE: number;
}

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

export class PyhmmerSearchService {
    /**
     * Execute a PyHMMER search
     */
    static async executeSearch(proteinSequence: string): Promise<PyhmmerSearchResult[]> {
        try {
            // Convert to FASTA format
            const fastaSequence = `>protein\n${proteinSequence}`;
            
            const searchRequest: PyhmmerSearchRequest = {
                database: 'bu_all',
                threshold: 'evalue',
                threshold_value: 0.01,
                input: fastaSequence,
                E: 0.01,
                domE: 0.01,
                incE: 0.01,
                incdomE: 0.01
            };
            
            const response = await PyhmmerService.search(searchRequest);
            
            if (response.id) {
                // Poll for results
                const results = await this.pollJobStatus(response.id);
                return results;
            } else {
                throw new Error('Failed to submit search');
            }
        } catch (error: any) {
            console.error('PyHMMER search error:', error);
            throw error;
        }
    }

    /**
     * Poll job status until completion
     */
    private static async pollJobStatus(jobId: string): Promise<PyhmmerSearchResult[]> {
        const maxAttempts = 30;
        let attempts = 0;
        
        while (attempts < maxAttempts) {
            try {
                const jobDetails = await PyhmmerService.getJobDetails(jobId);
                const status = jobDetails.status;
                
                if (status === 'completed' || status === 'SUCCESS') {
                    const results = jobDetails.task?.result || [];
                    
                    // Handle different result formats
                    if (Array.isArray(results)) {
                        return results;
                    } else if (results && typeof results === 'object') {
                        // If results is an object, try to extract the array
                        const resultKeys = Object.keys(results);
                        
                        // Look for common result array keys
                        for (const key of ['hits', 'domains', 'results', 'data']) {
                            if (Array.isArray(results[key])) {
                                return results[key];
                            }
                        }
                        
                        // If no array found, return the object as a single result
                        return [results];
                    } else {
                        return [];
                    }
                } else if (status === 'failed' || status === 'FAILED') {
                    throw new Error('PyHMMER search failed');
                }
                
                await new Promise(resolve => setTimeout(resolve, 2000));
                attempts++;
            } catch (error) {
                console.error('Error polling job status:', error);
                throw error;
            }
        }
        throw new Error('PyHMMER search timed out');
    }

    /**
     * Format E-value for display
     */
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

    /**
     * Format score for display
     */
    static formatScore(scoreRaw: string | number): string {
        const score = typeof scoreRaw === 'string' ? parseFloat(scoreRaw) : Number(scoreRaw);
        
        if (!isNaN(score) && isFinite(score)) {
            return score.toFixed(1);
        } else {
            return String(scoreRaw);
        }
    }

    /**
     * Check if a result is significant
     */
    static isResultSignificant(result: PyhmmerSearchResult): boolean {
        const isSignificant = result.is_significant || result.significant || result.significant_match || result.significantMatch;
        return isSignificant === true || isSignificant === 'true';
    }

    /**
     * Get target name from result
     */
    static getTargetName(result: PyhmmerSearchResult): string {
        return result.target_name || result.name || result.target || result.query || 'Unknown';
    }

    /**
     * Generate genome viewer URL for a locus tag
     */
    static generateGenomeViewerUrl(targetName: string): string {
        const strainPrefix = targetName.substring(0, targetName.lastIndexOf('_'));
        return `/genome/${strainPrefix}?locus_tag=${encodeURIComponent(targetName)}`;
    }
}
