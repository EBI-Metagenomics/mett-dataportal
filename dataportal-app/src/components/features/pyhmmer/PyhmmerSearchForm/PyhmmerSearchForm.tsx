import React, {useEffect, useState} from 'react';
import styles from './PyhmmerSearchForm.module.scss';
import {
    loadSearchHistory,
    PyhmmerService,
    removeFromHistory as removeFromHistoryService,
    saveSearchToHistory
} from '../../../../services/pyhmmer';
import {PyhmmerMXChoice, PyhmmerResult} from "../../../../interfaces/Pyhmmer";
import PyhmmerResultsTable from "../PyhmmerResultsHandler/PyhmmerResultsTable";
import PyhmmerSearchInput from "./PyhmmerSearchInput";
import PyhmmerSearchHistory from "./PyhmmerSearchHistory";
import { ThresholdTypeSelector, CutoffParameters, GapPenalties, InfoPopover, DatabaseSelector } from "./components";
import {SearchHistoryItem} from '../../../../utils/pyhmmer';
import {PYHMMER_CUTOFF_HELP, PYHMMER_GAP_PENALTIES_HELP} from '../../../../utils/pyhmmer';
import { usePyhmmerSearchForm } from '../../../../hooks/usePyhmmerSearchForm';


// Validation functions are now imported from utils/pyhmmer/validation

const PyhmmerSearchForm: React.FC = () => {
    // Use custom hook for form state management
    const {
        evalueType, setEvalueType,
        sequence, setSequence,
        database, setDatabase,
        significanceEValueSeq, setSignificanceEValueSeq,
        significanceEValueHit, setSignificanceEValueHit,
        reportEValueSeq, setReportEValueSeq,
        reportEValueHit, setReportEValueHit,
        significanceBitScoreSeq, setSignificanceBitScoreSeq,
        significanceBitScoreHit, setSignificanceBitScoreHit,
        reportBitScoreSeq, setReportBitScoreSeq,
        reportBitScoreHit, setReportBitScoreHit,
        gapOpen, setGapOpen,
        gapExtend, setGapExtend,
        getFieldError,
        isFormValid,
        resetForm
    } = usePyhmmerSearchForm();

    // Results state
    const [results, setResults] = useState<PyhmmerResult[]>([]);
    const [loading, setLoading] = useState(false);
    const [loadingMessage, setLoadingMessage] = useState<string>('');
    const [error, setError] = useState<string | undefined>(undefined);

    const [databases, setDatabases] = useState<{ id: string; name: string }[]>([]);
    const [mxChoices, setMXChoices] = useState<PyhmmerMXChoice[]>([]);

    // Search history state
    const [history, setHistory] = useState<SearchHistoryItem[]>([]);
    const [selectedJobId, setSelectedJobId] = useState<string | undefined>(undefined);
    const [currentSearchJobId, setCurrentSearchJobId] = useState<string | undefined>(undefined);

    // Load search history from localStorage
    const loadSearchHistoryLocal = () => {
        const history = loadSearchHistory();
        setHistory(history);
    };

    // Save search to history using centralized service
    const saveSearchToHistoryLocal = (jobId: string, query: string) => {
        const searchRequest = {
            database: database,
            threshold: evalueType,
            threshold_value: evalueType === 'evalue' ? parseFloat(significanceEValueSeq) : parseFloat(significanceBitScoreSeq),
            input: query
        };
        saveSearchToHistory(jobId, searchRequest);
        // Reload history to update UI
        loadSearchHistoryLocal();
    };

    // Remove item from history using centralized service
    const removeFromHistory = (jobId: string) => {
        try {
            removeFromHistoryService(jobId);
            // Reload history to update UI
            loadSearchHistoryLocal();
        } catch (error) {
            console.error('Error removing item from history:', error);
        }
    };

    useEffect(() => {
        const fetchDatabases = async () => {
            try {
                const response = await PyhmmerService.getDatabases();
                setDatabases(response);
            } catch (error) {
                console.error('Failed to fetch databases:', error);
                setDatabases([]);
                setError('Unable to load databases. Please check if the backend server is running.');
            }
        };

        fetchDatabases();

        loadSearchHistoryLocal();
    }, []);

    // Helper to poll for job status
    const pollJobStatus = async (jobId: string, maxAttempts = 60, delay = 2000) => {
        let attempts = 0;
        console.log(`=== STARTING POLLING FOR JOB ${jobId} ===`);
        console.log(`Max attempts: ${maxAttempts}, Delay: ${delay}ms`);

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

    // Map backend result to PyhmmerResult[]
    const mapResults = (raw: Record<string, unknown>[]): PyhmmerResult[] => {
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
            domains: (hit.domains || []) as any[], // Include domains from backend
        }));
    };

    // Handle new search submit
    const handleSubmit = async (e?: React.FormEvent) => {
        if (e) e.preventDefault();

        // Validate form before submission
        if (!isFormValid()) {
            setError('Please fix the validation errors before submitting.');
            return;
        }

        setLoading(true);
        setLoadingMessage('Submitting search job...');
        setError(undefined);
        setResults([]);
        try {
            // Compose request with all parameters
            const req = {
                database,
                threshold: evalueType,
                threshold_value: evalueType === 'evalue' ? parseFloat(significanceEValueSeq) : parseFloat(significanceBitScoreSeq),
                input: sequence,
                // Temporarily disabled - PyHMMER only supports default scoring matrix
                // mx: subMatrix,
                // E-value parameters
                E: evalueType === 'evalue' ? parseFloat(reportEValueSeq) : null,
                domE: evalueType === 'evalue' ? parseFloat(reportEValueHit) : null,
                incE: evalueType === 'evalue' ? parseFloat(significanceEValueSeq) : null,
                incdomE: evalueType === 'evalue' ? parseFloat(significanceEValueHit) : null,
                // Bit score parameters
                T: evalueType === 'bitscore' ? parseFloat(reportBitScoreSeq) : null,
                domT: evalueType === 'bitscore' ? parseFloat(reportBitScoreHit) : null,
                incT: evalueType === 'bitscore' ? parseFloat(significanceBitScoreSeq) : null,
                incdomT: evalueType === 'bitscore' ? parseFloat(significanceBitScoreHit) : null,
                // Gap penalties
                popen: parseFloat(gapOpen),
                pextend: parseFloat(gapExtend),
            };

            // Enhanced logging for form values
            console.log('=== FORM VALUES BEING SENT ===');
            console.log('Database:', database);
            console.log('Threshold type:', evalueType);
            console.log('Threshold value:', evalueType === 'evalue' ? parseFloat(significanceEValueSeq) : parseFloat(significanceBitScoreSeq));
            // Temporarily disabled - PyHMMER only supports default scoring matrix
            // console.log('Substitution matrix:', subMatrix);
            console.log('Input sequence length:', sequence.length);

            // E-value parameters
            console.log('=== E-VALUE FORM VALUES ===');
            console.log('Significance E-value (Sequence):', significanceEValueSeq);
            console.log('Significance E-value (Hit):', significanceEValueHit);
            console.log('Report E-value (Sequence):', reportEValueSeq);
            console.log('Report E-value (Hit):', reportEValueHit);

            // Bit score parameters
            console.log('=== BIT SCORE FORM VALUES ===');
            console.log('Significance Bit Score (Sequence):', significanceBitScoreSeq);
            console.log('Significance Bit Score (Hit):', significanceBitScoreHit);
            console.log('Report Bit Score (Sequence):', reportBitScoreSeq);
            console.log('Report Bit Score (Hit):', reportBitScoreHit);

            // Gap penalties
            console.log('=== GAP PENALTIES FORM VALUES ===');
            console.log('Gap open penalty:', gapOpen);
            console.log('Gap extend penalty:', gapExtend);

            console.log('=== FINAL REQUEST OBJECT ===');
            console.log('Request object:', req);

            setLoadingMessage('Creating search job...');
            const {id} = await PyhmmerService.search(req);
            console.log('PyhmmerService.search: Search submitted successfully, job ID:', id);

            // Set the current search job ID for domain fetching
            setCurrentSearchJobId(id);

            setLoadingMessage('Search submitted successfully!');
            setLoading(false);

            // Save to history
            saveSearchToHistoryLocal(id, sequence);

            // Start polling for results
            setLoading(true);
            setLoadingMessage('Waiting for results...');
            const searchResults = await pollJobStatus(id);

            // Set the results to state so they display in the UI
            console.log('=== RESULTS PROCESSING ===');
            console.log('Raw search results:', searchResults);
            console.log('Results type:', typeof searchResults);
            console.log('Results is array:', Array.isArray(searchResults));
            console.log('Results length:', Array.isArray(searchResults) ? searchResults.length : 'N/A');

            if (searchResults && Array.isArray(searchResults)) {
                const mappedResults = mapResults(searchResults);
                console.log('Mapped results:', mappedResults);
                console.log('Mapped results length:', mappedResults.length);
                setResults(mappedResults);
                setLoadingMessage(`Search completed! Found ${searchResults.length} results.`);
            } else {
                console.error('Invalid search results:', searchResults);
                setError('No results returned from search');
                setLoadingMessage('');
            }
        } catch (error) {
            console.error('Search error:', error);

            // Handle different types of errors
            if (error instanceof Error) {
                setError(error.message || 'Error running search');
            } else {
                setError('An unknown error occurred while running the search.');
            }
            setLoadingMessage('');
        } finally {
            setLoading(false);
        }
    };

    // Handle selecting a past search
    const handleSelectHistory = async (jobId: string) => {
        setSelectedJobId(jobId);
        setCurrentSearchJobId(undefined); // Clear current search job ID
        setLoading(true);
        setError(undefined);
        setResults([]);
        try {
            const job = await PyhmmerService.getJobDetails(jobId);
            if (job.status === 'SUCCESS' && job.task && Array.isArray(job.task.result)) {
                setResults(mapResults(job.task.result));
            } else {
                setError('No results found for this job.');
            }
        } catch {
            setError('Failed to load past search results.');
        } finally {
            setLoading(false);
        }
    };

    // Reset form to default values
    const handleReset = () => {
        // Use the form hook's reset function
        resetForm();

        // Clear results and job IDs
        setResults([]);
        setCurrentSearchJobId(undefined);
        setSelectedJobId(undefined);
        setError(undefined);
    };

    // Debug logging for job ID
    console.log('PyhmmerSearchForm: currentSearchJobId:', currentSearchJobId);
    console.log('PyhmmerSearchForm: selectedJobId:', selectedJobId);
    console.log('PyhmmerSearchForm: jobId being passed to results table:', currentSearchJobId || selectedJobId);

    return (
        <section className={styles.pyhmmerSection}>
            <div className={styles.formContainer}>
                <div className={styles.leftPane}>

                    {/* Cut off */}
                    <div className={styles.formSection}>
                        <InfoPopover
                            label="Cut off"
                            helpText={PYHMMER_CUTOFF_HELP}
                            ariaLabel="Cut off info"
                        />
                        <ThresholdTypeSelector
                            evalueType={evalueType}
                            onEvalueTypeChange={setEvalueType}
                        />
                        <CutoffParameters
                            evalueType={evalueType}
                            significanceEValueSeq={significanceEValueSeq}
                            significanceEValueHit={significanceEValueHit}
                            reportEValueSeq={reportEValueSeq}
                            reportEValueHit={reportEValueHit}
                            significanceBitScoreSeq={significanceBitScoreSeq}
                            significanceBitScoreHit={significanceBitScoreHit}
                            reportBitScoreSeq={reportBitScoreSeq}
                            reportBitScoreHit={reportBitScoreHit}
                            setSignificanceEValueSeq={setSignificanceEValueSeq}
                            setSignificanceEValueHit={setSignificanceEValueHit}
                            setReportEValueSeq={setReportEValueSeq}
                            setReportEValueHit={setReportEValueHit}
                            setSignificanceBitScoreSeq={setSignificanceBitScoreSeq}
                            setSignificanceBitScoreHit={setSignificanceBitScoreHit}
                            setReportBitScoreSeq={setReportBitScoreSeq}
                            setReportBitScoreHit={setReportBitScoreHit}
                            getFieldError={getFieldError}
                        />
                    </div>

                    <div className={styles.sectionDivider}></div>

                    {/* Gap penalties */}
                    <div className={styles.formSection}>
                        <InfoPopover
                            label="Gap penalties"
                            helpText={PYHMMER_GAP_PENALTIES_HELP}
                            ariaLabel="Gap penalties info"
                        />
                        <GapPenalties
                            gapOpen={gapOpen}
                            gapExtend={gapExtend}
                            setGapOpen={setGapOpen}
                            setGapExtend={setGapExtend}
                            getFieldError={getFieldError}
                        />
                    </div>

                </div>
                <div className={styles.rightPane}>
                    {/* Sequence database */}
                    <DatabaseSelector
                        database={database}
                        databases={databases}
                        onDatabaseChange={setDatabase}
                    />

                    {/* <div className={`${styles.sectionDivider} ${styles.tight}`}></div> */}

                    <PyhmmerSearchInput
                        sequence={sequence}
                        setSequence={setSequence}
                        handleSubmit={handleSubmit}
                        sequenceError={getFieldError('sequence')}
                        isFormValid={isFormValid()}
                        onResetAll={handleReset}
                    />
                </div>
            </div>

            {/* Section divider between form and results */}
            <div className={styles.sectionDivider}></div>

            {/* Results two-column layout */}
            <div className={styles.resultsContainer}>
                <div className={styles.historyPane}>
                    <PyhmmerSearchHistory
                        history={history}
                        onSelect={handleSelectHistory}
                        selectedJobId={selectedJobId}
                        onDelete={removeFromHistory}
                    />
                </div>
                <div className={styles.resultsPane}>
                    <PyhmmerResultsTable
                        results={results}
                        loading={loading}
                        loadingMessage={loadingMessage}
                        error={error}
                        jobId={currentSearchJobId || selectedJobId}
                    />
                </div>
            </div>
        </section>
    );
};

export default PyhmmerSearchForm;