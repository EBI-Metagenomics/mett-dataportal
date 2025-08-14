import { PyhmmerService } from '../../services/pyhmmerService';
import { PyhmmerResult } from '../../interfaces/Pyhmmer';

/**
 * Search request interface
 */
export interface PyhmmerSearchRequest {
    database: string;
    threshold: 'evalue' | 'bitscore';
    threshold_value: number;
    input: string;
    E?: number | null;
    domE?: number | null;
    incE?: number | null;
    incdomE?: number | null;
    T?: number | null;
    domT?: number | null;
    incT?: number | null;
    incdomT?: number | null;
    popen?: number;
    pextend?: number;
    mx?: string;
}

/**
 * Search result interface
 */
export interface PyhmmerSearchResult {
    jobId: string;
    results: PyhmmerResult[];
}

/**
 * Poll for search results
 */
export const pollJobStatus = async (jobId: string, maxAttempts = 30, delay = 10000): Promise<any[]> => {
    let attempts = 0;

    console.log(`=== STARTING POLLING FOR JOB ${jobId} ===`);

    while (attempts < maxAttempts) {
        attempts++;
        console.log(`Polling attempt ${attempts}/${maxAttempts} for job ${jobId}`);

        try {
            const job = await PyhmmerService.getJobDetails(jobId);
            console.log(`Job details received:`, job);
            console.log(`Job status: ${job.status}`);
            console.log(`Job task status: ${job.task?.status}`);
            console.log(`Job task result type: ${typeof job.task?.result}`);
            console.log(`Job task result length: ${Array.isArray(job.task?.result) ? job.task?.result.length : 'N/A'}`);

            if (job.status === 'SUCCESS' && job.task && Array.isArray(job.task.result)) {
                console.log(`Job ${jobId} completed successfully with ${job.task.result.length} results`);
                console.log(`First result:`, job.task.result[0]);
                console.log(`=== POLLING COMPLETED SUCCESSFULLY ===`);
                return job.task.result;
            } else if (job.status === 'FAILURE') {
                console.error(`Job ${jobId} failed`);
                console.error(`Job task result:`, job.task?.result);
                throw new Error('Job failed');
            } else if (job.status === 'STARTED' || job.status === 'PENDING') {
                console.log(`Job ${jobId} is still running (${job.status}), waiting...`);
                // Continue polling
            } else {
                console.log(`Job ${jobId} has unexpected status: ${job.status}`);
                console.log(`Full job response:`, job);
            }
        } catch (error) {
            console.error(`Error polling job ${jobId} (attempt ${attempts}):`, error);
            if (attempts === maxAttempts) {
                throw error;
            }
        }

        if (attempts < maxAttempts) {
            console.log(`Waiting ${delay}ms before next attempt...`);
            await new Promise(res => setTimeout(res, delay));
        }
    }

    console.error(`=== POLLING TIMED OUT ===`);
    console.error(`Job ${jobId} did not complete after ${maxAttempts} attempts (${maxAttempts * delay / 1000} seconds)`);
    throw new Error(`Timed out waiting for results after ${maxAttempts} attempts (${maxAttempts * delay / 1000} seconds)`);
};

/**
 * Map backend result to PyhmmerResult[]
 */
export const mapResults = (raw: Record<string, unknown>[]): PyhmmerResult[] => {
    return raw.map((hit: Record<string, unknown>) => ({
        query: (hit.query || hit.query_name || '-') as string,
        target: (hit.target || hit.target_name || hit.name || '-') as string,
        evalue: (hit.evalue ?? hit.Evalue ?? '-') as string,
        score: (hit.score ?? hit.Score ?? '-') as string,
        num_hits: (hit.num_hits ?? 0) as number,
        num_significant: (hit.num_significant ?? 0) as number,
        is_significant: (hit.is_significant ?? false) as boolean,
        bias: (hit.bias ?? 0) as number,
        description: (hit.description ?? hit.desc ?? '-') as string,
        domains: (hit.domains || []) as any[],
    }));
};

/**
 * Submit a PyHMMER search
 */
export const submitSearch = async (searchRequest: PyhmmerSearchRequest): Promise<string> => {
    try {
        console.log('=== SEARCH REQUEST RECEIVED ===');
        console.log('Search request:', searchRequest);

        // Start the search
        const searchResponse = await PyhmmerService.search(searchRequest);
        const jobId = searchResponse.id;
        console.log(`Search job started with ID: ${jobId}`);

        return jobId;
    } catch (error) {
        console.error('Search submission error:', error);
        throw error;
    }
};

/**
 * Execute a complete search workflow
 */
export const executeSearch = async (searchRequest: PyhmmerSearchRequest): Promise<PyhmmerSearchResult> => {
    try {
        // Submit the search
        const jobId = await submitSearch(searchRequest);
        
        // Poll for results
        const rawResults = await pollJobStatus(jobId);
        const mappedResults = mapResults(rawResults);

        return {
            jobId,
            results: mappedResults
        };
    } catch (error) {
        console.error('Search execution error:', error);
        throw error;
    }
};
