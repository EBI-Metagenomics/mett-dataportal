import React, {useEffect, useState} from 'react';
import styles from './PyhmmerSearchForm.module.scss';
import {PyhmmerService} from '../../../../services/pyhmmerService';
import {PyhmmerMXChoice, PyhmmerResult} from "../../../../interfaces/Pyhmmer";
import PyhmmerResultsTable from "@components/organisms/Pyhmmer/PyhmmerResultsHandler/PyhmmerResultsTable";
import PyhmmerSearchInput from "@components/organisms/Pyhmmer/PyhmmerSearchForm/PyhmmerSearchInput";
import PyhmmerSearchHistory, {
    SearchHistoryItem
} from "@components/organisms/Pyhmmer/PyhmmerSearchForm/PyhmmerSearchHistory";
import * as Popover from '@radix-ui/react-popover';
import {PYHMMER_CUTOFF_HELP, PYHMMER_FILTER_HELP, PYHMMER_GAP_PENALTIES_HELP} from '../../../../utils/constants';

const HISTORY_KEY = 'pyhmmer_search_history';

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

    // Bias composition filter
    const [turnOffBiasFilter, setTurnOffBiasFilter] = useState(false);

    // Temporarily disabled - PyHMMER only supports default scoring matrix
    // const [subMatrix, setSubMatrix] = useState('BLOSUM62');

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
        // Temporarily disabled - PyHMMER only supports default scoring matrix
        /*
        const fetchMXChoices = async () => {
            try {
                const response = await PyhmmerService.getMXChoices();
                setMXChoices(response);
            } catch (error) {
                console.error('Failed to fetch MX choices:', error);
                setMXChoices([]);
                setError('Unable to load substitution matrices. Please check if the backend server is running.');
            }
        };
        */
        fetchDatabases();
        // fetchMXChoices();
        // Load history from localStorage
        const stored = localStorage.getItem(HISTORY_KEY);
        if (stored) {
            setHistory(JSON.parse(stored));
        }
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
            bias: (hit.bias ?? 0) as number,
            description: (hit.description ?? hit.desc ?? '-') as string,
            domains: (hit.domains || []) as any[], // Include domains from backend
        }));
    };

    // Save search to localStorage
    const saveSearchToHistory = (jobId: string, query: string) => {
        const date = new Date().toLocaleString();
        const newItem: SearchHistoryItem = {jobId, query, date};
        let updated = [newItem, ...history.filter(h => h.jobId !== jobId)];
        // Limit to 20 most recent
        if (updated.length > 20) updated = updated.slice(0, 20);
        setHistory(updated);
        localStorage.setItem(HISTORY_KEY, JSON.stringify(updated));
    };

    // Handle new search submit
    const handleSubmit = async (e?: React.FormEvent) => {
        if (e) e.preventDefault();
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
                // Bias composition filter
                bias_filter: turnOffBiasFilter ? 'off' : 'on',
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

            // Bias composition filter
            console.log('=== BIAS COMPOSITION FILTER FORM VALUES ===');
            console.log('Turn off bias filter:', turnOffBiasFilter);

            console.log('=== FINAL REQUEST OBJECT ===');
            console.log('Request object:', req);

            setLoadingMessage('Creating search job...');
            const {id} = await PyhmmerService.search(req);
            console.log(`Search job created with ID: ${id}`);

            setLoadingMessage('Processing search results... This may take a few minutes.');
            const rawResults = await pollJobStatus(id);
            if (rawResults) {
                setResults(mapResults(rawResults));
                setSelectedJobId(id);
                saveSearchToHistory(id, sequence.slice(0, 40) + (sequence.length > 40 ? '...' : ''));
                setLoadingMessage('');
            }
        } catch (err) {
            console.error('Search error:', err);

            // Handle different types of errors
            if (err instanceof Error) {
                setError(err.message || 'Error running search');
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
                                    <input
                                        type="number"
                                        step="any"
                                        value={significanceEValueSeq}
                                        onChange={e => setSignificanceEValueSeq(e.target.value)}
                                        className={styles.input}
                                    />
                                    <input
                                        type="number"
                                        step="any"
                                        value={significanceEValueHit}
                                        onChange={e => setSignificanceEValueHit(e.target.value)}
                                        className={styles.input}
                                    />
                                    <div className={styles.cutoffLabel}>Report E-values</div>
                                    <input
                                        type="number"
                                        step="any"
                                        value={reportEValueSeq}
                                        onChange={e => setReportEValueSeq(e.target.value)}
                                        className={styles.input}
                                    />
                                    <input
                                        type="number"
                                        step="any"
                                        value={reportEValueHit}
                                        onChange={e => setReportEValueHit(e.target.value)}
                                        className={styles.input}
                                    />
                                </>
                            ) : (
                                <>
                                    <div className={styles.cutoffLabel}>Significance Bit scores</div>
                                    <input
                                        type="number"
                                        step="any"
                                        value={significanceBitScoreSeq}
                                        onChange={e => setSignificanceBitScoreSeq(e.target.value)}
                                        className={styles.input}
                                    />
                                    <input
                                        type="number"
                                        step="any"
                                        value={significanceBitScoreHit}
                                        onChange={e => setSignificanceBitScoreHit(e.target.value)}
                                        className={styles.input}
                                    />
                                    <div className={styles.cutoffLabel}>Report Bit scores</div>
                                    <input
                                        type="number"
                                        step="any"
                                        value={reportBitScoreSeq}
                                        onChange={e => setReportBitScoreSeq(e.target.value)}
                                        className={styles.input}
                                    />
                                    <input
                                        type="number"
                                        step="any"
                                        value={reportBitScoreHit}
                                        onChange={e => setReportBitScoreHit(e.target.value)}
                                        className={styles.input}
                                    />
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
                                <input
                                    type="number"
                                    step="any"
                                    value={gapOpen}
                                    onChange={e => setGapOpen(e.target.value)}
                                    className={styles.inputSmall}
                                />
                            </div>
                            <div>
                                <div className={styles.gapLabel}>Extend</div>
                                <input
                                    type="number"
                                    step="any"
                                    value={gapExtend}
                                    onChange={e => setGapExtend(e.target.value)}
                                    className={styles.inputSmall}
                                />
                            </div>
                        </div>
                    </div>

                    <div className={styles.sectionDivider}></div>

                    {/* Bias composition filter */}
                    <div className={styles.formSection}>
                        <div className={styles.flexRow}>
                            <label className={`vf-form__label ${styles.label}`}>Filter
                                <Popover.Root>
                                    <Popover.Trigger asChild>
                                        <button
                                            className={styles.infoIcon}
                                            onClick={e => e.stopPropagation()}
                                            aria-label="Filter info"
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
                                                <strong>Bias composition filter:</strong><br/>
                                                <p style={{whiteSpace: 'pre-line'}}>{PYHMMER_FILTER_HELP}</p>
                                            </div>
                                        </Popover.Content>
                                    </Popover.Portal>
                                </Popover.Root>
                            </label>
                        </div>
                        <div className={styles.checkboxRow}>
                            <label className={styles.checkboxLabel}>
                                <input
                                    type="checkbox"
                                    className={styles.checkboxInput}
                                    checked={turnOffBiasFilter}
                                    onChange={e => setTurnOffBiasFilter(e.target.checked)}
                                />
                                <span className={styles.checkboxText}>Turn off bias composition filter</span>
                            </label>
                        </div>
                    </div>
                </div>
                <div className={styles.rightPane}>
                    {/* Sequence database */}
                    <div className={styles.formSection}>
                        <label className={`vf-form__label ${styles.label}`}>Sequence database</label>
                        <select className={`vf-form__select ${styles.select}`} value={database}
                                onChange={e => setDatabase(e.target.value)}>
                            {databases.length > 0 ? (
                                databases.map(db => (
                                    <option key={db.id} value={db.id}>{db.name}</option>
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
                    />
                </div>
                <div className={styles.resultsPane}>
                    <PyhmmerResultsTable
                        results={results}
                        loading={loading}
                        loadingMessage={loadingMessage}
                        error={error}
                        jobId={selectedJobId}
                    />
                </div>
            </div>
        </section>
    );
};

export default PyhmmerSearchForm;