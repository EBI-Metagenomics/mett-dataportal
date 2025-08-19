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
import {SearchHistoryItem} from '../../../../utils/pyhmmer';
import * as Popover from '@radix-ui/react-popover';
import {PYHMMER_CUTOFF_HELP, PYHMMER_GAP_PENALTIES_HELP} from '../../../../utils/pyhmmer';


// Validation error interface
interface ValidationError {
    field: string;
    message: string;
}

// Validation functions
const validateEValue = (value: string, fieldName: string): ValidationError | null => {
    const numValue = parseFloat(value);
    if (isNaN(numValue)) {
        return {field: fieldName, message: 'Must be a valid number'};
    }
    if (numValue < 0 || numValue > 100.0) {
        return {field: fieldName, message: 'Must be between 0 and 100.0'};
    }
    return null;
};

const validateBitScore = (value: string, fieldName: string): ValidationError | null => {
    const numValue = parseFloat(value);
    if (isNaN(numValue)) {
        return {field: fieldName, message: 'Must be a valid number'};
    }
    if (numValue < 0.0 || numValue > 1000.0) {
        return {field: fieldName, message: 'Must be between 0.0 and 1000.0'};
    }
    return null;
};

const validateGapPenalty = (value: string, fieldName: string, maxValue: number): ValidationError | null => {
    const numValue = parseFloat(value);
    if (isNaN(numValue)) {
        return {field: fieldName, message: 'Must be a valid number'};
    }
    if (numValue < 0 || numValue >= maxValue) {
        return {field: fieldName, message: `Must be between 0 and ${maxValue}`};
    }
    return null;
};

const validateCutoffRelationships = (
    evalueType: 'evalue' | 'bitscore',
    significanceSeq: string,
    significanceHit: string,
    reportSeq: string,
    reportHit: string
): ValidationError[] => {
    const errors: ValidationError[] = [];

    if (evalueType === 'evalue') {
        const incE = parseFloat(significanceSeq);
        const incdomE = parseFloat(significanceHit);
        const E = parseFloat(reportSeq);
        const domE = parseFloat(reportHit);

        if (!isNaN(incE) && !isNaN(E) && incE > E) {
            errors.push({
                field: 'significanceEValueSeq',
                message: 'Significance E-value (Sequence) should be ≤ Report E-value (Sequence)'
            });
        }
        if (!isNaN(incdomE) && !isNaN(domE) && incdomE > domE) {
            errors.push({
                field: 'significanceEValueHit',
                message: 'Significance E-value (Hit) should be ≤ Report E-value (Hit)'
            });
        }
    } else {
        const incT = parseFloat(significanceSeq);
        const incdomT = parseFloat(significanceHit);
        const T = parseFloat(reportSeq);
        const domT = parseFloat(reportHit);

        if (!isNaN(incT) && !isNaN(T) && incT < T) {
            errors.push({
                field: 'significanceBitScoreSeq',
                message: 'Significance Bit Score (Sequence) should be ≥ Report Bit Score (Sequence)'
            });
        }
        if (!isNaN(incdomT) && !isNaN(domT) && incdomT < domT) {
            errors.push({
                field: 'significanceBitScoreHit',
                message: 'Significance Bit Score (Hit) should be ≥ Report Bit Score (Hit)'
            });
        }
    }

    return errors;
};

const PyhmmerSearchForm: React.FC = () => {
    const [evalueType, setEvalueType] = useState<'evalue' | 'bitscore'>('evalue');
    const [sequence, setSequence] = useState('');
    const [database, setDatabase] = useState('bu_all');

    // Cutoff parameters
    const [significanceEValueSeq, setSignificanceEValueSeq] = useState('0.01');
    const [significanceEValueHit, setSignificanceEValueHit] = useState('0.03');
    const [reportEValueSeq, setReportEValueSeq] = useState('1');
    const [reportEValueHit, setReportEValueHit] = useState('1');
    const [significanceBitScoreSeq, setSignificanceBitScoreSeq] = useState('25');
    const [significanceBitScoreHit, setSignificanceBitScoreHit] = useState('22');
    const [reportBitScoreSeq, setReportBitScoreSeq] = useState('7');
    const [reportBitScoreHit, setReportBitScoreHit] = useState('5');

    // Gap penalties
    const [gapOpen, setGapOpen] = useState('0.02');
    const [gapExtend, setGapExtend] = useState('0.4');

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

    // Validation state
    const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);

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

    // Validation function
    const validateForm = (): ValidationError[] => {
        const errors: ValidationError[] = [];

        // Validate sequence
        // if (!sequence.trim()) {
        //     errors.push({ field: 'sequence', message: 'Sequence is required' });
        // }

        // Validate E-value parameters when E-value is selected
        if (evalueType === 'evalue') {
            const incEError = validateEValue(significanceEValueSeq, 'significanceEValueSeq');
            if (incEError) errors.push(incEError);

            const incdomEError = validateEValue(significanceEValueHit, 'significanceEValueHit');
            if (incdomEError) errors.push(incdomEError);

            const EError = validateEValue(reportEValueSeq, 'reportEValueSeq');
            if (EError) errors.push(EError);

            const domEError = validateEValue(reportEValueHit, 'reportEValueHit');
            if (domEError) errors.push(domEError);
        }

        // Validate Bit Score parameters when Bit Score is selected
        if (evalueType === 'bitscore') {
            const incTError = validateBitScore(significanceBitScoreSeq, 'significanceBitScoreSeq');
            if (incTError) errors.push(incTError);

            const incdomTError = validateBitScore(significanceBitScoreHit, 'significanceBitScoreHit');
            if (incdomTError) errors.push(incdomTError);

            const TError = validateBitScore(reportBitScoreSeq, 'reportBitScoreSeq');
            if (TError) errors.push(TError);

            const domTError = validateBitScore(reportBitScoreHit, 'reportBitScoreHit');
            if (domTError) errors.push(domTError);
        }

        // Validate gap penalties
        const gapOpenError = validateGapPenalty(gapOpen, 'gapOpen', 0.5);
        if (gapOpenError) errors.push(gapOpenError);

        const gapExtendError = validateGapPenalty(gapExtend, 'gapExtend', 1.0);
        if (gapExtendError) errors.push(gapExtendError);

        // Validate cutoff relationships
        const relationshipErrors = validateCutoffRelationships(
            evalueType,
            evalueType === 'evalue' ? significanceEValueSeq : significanceBitScoreSeq,
            evalueType === 'evalue' ? significanceEValueHit : significanceBitScoreHit,
            evalueType === 'evalue' ? reportEValueSeq : reportBitScoreSeq,
            evalueType === 'evalue' ? reportEValueHit : reportBitScoreHit
        );
        errors.push(...relationshipErrors);

        return errors;
    };

    // Get error for a specific field
    const getFieldError = (fieldName: string): string | undefined => {
        return validationErrors.find(error => error.field === fieldName)?.message;
    };

    // Check if form is valid
    const isFormValid = (): boolean => {
        return validationErrors.length === 0;
    };

    // Update validation errors when form values change
    useEffect(() => {
        const errors = validateForm();
        setValidationErrors(errors);
    }, [
        sequence, evalueType,
        significanceEValueSeq, significanceEValueHit, reportEValueSeq, reportEValueHit,
        significanceBitScoreSeq, significanceBitScoreHit, reportBitScoreSeq, reportBitScoreHit,
        gapOpen, gapExtend
    ]);

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
        const errors = validateForm();
        if (errors.length > 0) {
            setValidationErrors(errors);
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
        setEvalueType('evalue');
        setSequence('');
        setDatabase('bu_all');

        // Cutoff parameters
        setSignificanceEValueSeq('0.01');
        setSignificanceEValueHit('0.03');
        setReportEValueSeq('1');
        setReportEValueHit('1');
        setSignificanceBitScoreSeq('25');
        setSignificanceBitScoreHit('22');
        setReportBitScoreSeq('7');
        setReportBitScoreHit('5');

        // Gap penalties
        setGapOpen('0.02');
        setGapExtend('0.4');

        // Clear results and job IDs
        setResults([]);
        setCurrentSearchJobId(undefined);
        setSelectedJobId(undefined);

        // Validation errors
        setValidationErrors([]);
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
                        <div className={styles.flexRow}>
                            <label className={`vf-form__label ${styles.label}`}>Cut off
                                <Popover.Root>
                                    <Popover.Trigger asChild>
                                        <button
                                            className={styles.infoIcon}
                                            onClick={e => e.stopPropagation()}
                                            aria-label="Cut off info"
                                            type="button"
                                        >
                                            ℹ️
                                        </button>
                                    </Popover.Trigger>
                                    <Popover.Portal>
                                        <Popover.Content
                                            className={styles.popoverContent}
                                            side="top"
                                            align="end"
                                            sideOffset={5}
                                        >
                                            <div className={styles.popoverInner}>
                                                <strong>Cut off parameters:</strong><br/>
                                                <p style={{whiteSpace: 'pre-line'}}>{PYHMMER_CUTOFF_HELP}</p>
                                            </div>
                                        </Popover.Content>
                                    </Popover.Portal>
                                </Popover.Root>
                            </label>
                        </div>
                        <div className={styles.radioRow}>
                            <label className={styles.radioLabel}>
                                <input
                                    type="radio"
                                    className={styles.radioInput}
                                    checked={evalueType === 'evalue'}
                                    onChange={() => setEvalueType('evalue')}
                                />
                                <span className={styles.radioText}>E-value</span>
                            </label>
                            <label className={styles.radioLabel}>
                                <input
                                    type="radio"
                                    className={styles.radioInput}
                                    checked={evalueType === 'bitscore'}
                                    onChange={() => setEvalueType('bitscore')}
                                />
                                <span className={styles.radioText}>Bit Score</span>
                            </label>
                        </div>
                        <div className={styles.cutoffGrid}>
                            <div></div>
                            <div className={styles.cutoffHeader}>Sequence</div>
                            <div className={styles.cutoffHeader}>Hit</div>

                            {evalueType === 'evalue' ? (
                                <>
                                    <div className={styles.cutoffLabel}>Significance E-values</div>
                                    <div className={styles.inputContainer}>
                                        <input
                                            type="number"
                                            step="any"
                                            value={significanceEValueSeq}
                                            onChange={e => setSignificanceEValueSeq(e.target.value)}
                                            className={`${styles.input} ${getFieldError('significanceEValueSeq') ? styles.inputError : ''}`}
                                        />
                                        {getFieldError('significanceEValueSeq') && (
                                            <div
                                                className={styles.errorMessage}>{getFieldError('significanceEValueSeq')}</div>
                                        )}
                                    </div>
                                    <div className={styles.inputContainer}>
                                        <input
                                            type="number"
                                            step="any"
                                            value={significanceEValueHit}
                                            onChange={e => setSignificanceEValueHit(e.target.value)}
                                            className={`${styles.input} ${getFieldError('significanceEValueHit') ? styles.inputError : ''}`}
                                        />
                                        {getFieldError('significanceEValueHit') && (
                                            <div
                                                className={styles.errorMessage}>{getFieldError('significanceEValueHit')}</div>
                                        )}
                                    </div>
                                    <div className={styles.cutoffLabel}>Report E-values</div>
                                    <div className={styles.inputContainer}>
                                        <input
                                            type="number"
                                            step="any"
                                            value={reportEValueSeq}
                                            onChange={e => setReportEValueSeq(e.target.value)}
                                            className={`${styles.input} ${getFieldError('reportEValueSeq') ? styles.inputError : ''}`}
                                        />
                                        {getFieldError('reportEValueSeq') && (
                                            <div
                                                className={styles.errorMessage}>{getFieldError('reportEValueSeq')}</div>
                                        )}
                                    </div>
                                    <div className={styles.inputContainer}>
                                        <input
                                            type="number"
                                            step="any"
                                            value={reportEValueHit}
                                            onChange={e => setReportEValueHit(e.target.value)}
                                            className={`${styles.input} ${getFieldError('reportEValueHit') ? styles.inputError : ''}`}
                                        />
                                        {getFieldError('reportEValueHit') && (
                                            <div
                                                className={styles.errorMessage}>{getFieldError('reportEValueHit')}</div>
                                        )}
                                    </div>
                                </>
                            ) : (
                                <>
                                    <div className={styles.cutoffLabel}>Significance Bit scores</div>
                                    <div className={styles.inputContainer}>
                                        <input
                                            type="number"
                                            step="any"
                                            value={significanceBitScoreSeq}
                                            onChange={e => setSignificanceBitScoreSeq(e.target.value)}
                                            className={`${styles.input} ${getFieldError('significanceBitScoreSeq') ? styles.inputError : ''}`}
                                        />
                                        {getFieldError('significanceBitScoreSeq') && (
                                            <div
                                                className={styles.errorMessage}>{getFieldError('significanceBitScoreSeq')}</div>
                                        )}
                                    </div>
                                    <div className={styles.inputContainer}>
                                        <input
                                            type="number"
                                            step="any"
                                            value={significanceBitScoreHit}
                                            onChange={e => setSignificanceBitScoreHit(e.target.value)}
                                            className={`${styles.input} ${getFieldError('significanceBitScoreHit') ? styles.inputError : ''}`}
                                        />
                                        {getFieldError('significanceBitScoreHit') && (
                                            <div
                                                className={styles.errorMessage}>{getFieldError('significanceBitScoreHit')}</div>
                                        )}
                                    </div>
                                    <div className={styles.cutoffLabel}>Report Bit scores</div>
                                    <div className={styles.inputContainer}>
                                        <input
                                            type="number"
                                            step="any"
                                            value={reportBitScoreSeq}
                                            onChange={e => setReportBitScoreSeq(e.target.value)}
                                            className={`${styles.input} ${getFieldError('reportBitScoreSeq') ? styles.inputError : ''}`}
                                        />
                                        {getFieldError('reportBitScoreSeq') && (
                                            <div
                                                className={styles.errorMessage}>{getFieldError('reportBitScoreSeq')}</div>
                                        )}
                                    </div>
                                    <div className={styles.inputContainer}>
                                        <input
                                            type="number"
                                            step="any"
                                            value={reportBitScoreHit}
                                            onChange={e => setReportBitScoreHit(e.target.value)}
                                            className={`${styles.input} ${getFieldError('reportBitScoreHit') ? styles.inputError : ''}`}
                                        />
                                        {getFieldError('reportBitScoreHit') && (
                                            <div
                                                className={styles.errorMessage}>{getFieldError('reportBitScoreHit')}</div>
                                        )}
                                    </div>
                                </>
                            )}
                        </div>
                    </div>

                    <div className={styles.sectionDivider}></div>

                    {/* Gap penalties */}
                    <div className={styles.formSection}>
                        <div className={styles.flexRow}>
                            <label className={`vf-form__label ${styles.label}`}>Gap penalties
                                <Popover.Root>
                                    <Popover.Trigger asChild>
                                        <button
                                            className={styles.infoIcon}
                                            onClick={e => e.stopPropagation()}
                                            aria-label="Gap penalties info"
                                            type="button"
                                        >
                                            ℹ️
                                        </button>
                                    </Popover.Trigger>
                                    <Popover.Portal>
                                        <Popover.Content
                                            className={styles.popoverContent}
                                            side="top"
                                            align="end"
                                            sideOffset={5}
                                        >
                                            <div className={styles.popoverInner}>
                                                <strong>Gap penalties:</strong><br/>
                                                <p style={{whiteSpace: 'pre-line'}}>{PYHMMER_GAP_PENALTIES_HELP}</p>
                                            </div>
                                        </Popover.Content>
                                    </Popover.Portal>
                                </Popover.Root>
                            </label>
                        </div>
                        <div className={styles.gapRow}>
                            <div>
                                <div className={styles.gapLabel}>Open</div>
                                <div className={styles.inputContainer}>
                                    <input
                                        type="number"
                                        step="any"
                                        value={gapOpen}
                                        onChange={e => setGapOpen(e.target.value)}
                                        className={`${styles.inputSmall} ${getFieldError('gapOpen') ? styles.inputError : ''}`}
                                    />
                                    {getFieldError('gapOpen') && (
                                        <div className={styles.errorMessage}>{getFieldError('gapOpen')}</div>
                                    )}
                                </div>
                            </div>
                            <div>
                                <div className={styles.gapLabel}>Extend</div>
                                <div className={styles.inputContainer}>
                                    <input
                                        type="number"
                                        step="any"
                                        value={gapExtend}
                                        onChange={e => setGapExtend(e.target.value)}
                                        className={`${styles.inputSmall} ${getFieldError('gapExtend') ? styles.inputError : ''}`}
                                    />
                                    {getFieldError('gapExtend') && (
                                        <div className={styles.errorMessage}>{getFieldError('gapExtend')}</div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>

                </div>
                <div className={styles.rightPane}>
                    {/* Sequence database */}
                    <div className={styles.formSection}>
                        <label className={`vf-form__label ${styles.label}`}>Sequence database</label>
                        <select
                            className={`vf-form__select ${styles.databaseSelect}`}
                            value={database}
                            onChange={e => setDatabase(e.target.value)}
                        >
                            {databases.length > 0 ? (
                                databases.map(db => (
                                    <option key={db.id} value={db.id}>
                                        {db.name}
                                    </option>
                                ))
                            ) : (
                                <option value="">No databases available</option>
                            )}
                        </select>
                    </div>

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