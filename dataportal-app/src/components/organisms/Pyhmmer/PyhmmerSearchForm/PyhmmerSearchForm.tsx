import React, {useState, useEffect} from 'react';
import styles from './PyhmmerSearchForm.module.scss';
import {PyhmmerService} from '../../../../services/pyhmmerService';
import {PyhmmerMXChoice, PyhmmerResult} from "../../../../interfaces/Pyhmmer";
import PyhmmerResultsTable from "@components/organisms/Pyhmmer/PyhmmerResultsHandler/PyhmmerResultsTable";
import PyhmmerSearchInput from "@components/organisms/Pyhmmer/PyhmmerSearchForm/PyhmmerSearchInput";
import PyhmmerSearchHistory, { SearchHistoryItem } from "@components/organisms/Pyhmmer/PyhmmerSearchForm/PyhmmerSearchHistory";

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
    const [subMatrix, setSubMatrix] = useState('BLOSUM62');

    // Results state
    const [results, setResults] = useState<PyhmmerResult[]>([]);
    const [loading, setLoading] = useState(false);
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
            } catch {
                setDatabases([]);
            }
        };
        const fetchMXChoices = async () => {
            try {
                const response = await PyhmmerService.getMXChoices();
                setMXChoices(response);
            } catch {
                setMXChoices([]);
            }
        };
        fetchDatabases();
        fetchMXChoices();
        // Load history from localStorage
        const stored = localStorage.getItem(HISTORY_KEY);
        if (stored) {
            setHistory(JSON.parse(stored));
        }
    }, []);

    // Helper to poll for job status
    const pollJobStatus = async (jobId: string, maxAttempts = 20, delay = 1500) => {
        let attempts = 0;
        while (attempts < maxAttempts) {
            const job = await PyhmmerService.getJobDetails(jobId);
            if (job.status === 'SUCCESS' && job.task && Array.isArray(job.task.result)) {
                return job.task.result;
            } else if (job.status === 'FAILURE') {
                throw new Error('Job failed');
            }
            await new Promise(res => setTimeout(res, delay));
            attempts++;
        }
        throw new Error('Timed out waiting for results');
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
        }));
    };

    // Save search to localStorage
    const saveSearchToHistory = (jobId: string, query: string) => {
        const date = new Date().toLocaleString();
        const newItem: SearchHistoryItem = { jobId, query, date };
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
        setError(undefined);
        setResults([]);
        try {
            // Compose request with all parameters
            const req = {
                database,
                threshold: evalueType,
                threshold_value: evalueType === 'evalue' ? parseFloat(significanceEValueSeq) : parseFloat(significanceBitScoreSeq),
                input: sequence,
                mx: subMatrix,
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
            const {id} = await PyhmmerService.search(req);
            const rawResults = await pollJobStatus(id);
            if (rawResults) {
                setResults(mapResults(rawResults));
                setSelectedJobId(id);
                saveSearchToHistory(id, sequence.slice(0, 40) + (sequence.length > 40 ? '...' : ''));
            }
        } catch (err) {
            if (err instanceof Error) {
                setError(err.message || 'Error running search');
            } else {
                setError('An unknown error occurred while running the search.');
            }
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
                    {/* Sequence database */}
                    <div className={styles.formSection}>
                        <label className={styles.label}>Sequence database</label>
                        <select className={styles.select} value={database} onChange={e => setDatabase(e.target.value)}>
                            {databases.map(db => (
                                <option key={db.id} value={db.id}>{db.name}</option>
                            ))}
                        </select>
                    </div>

                    {/* Cut off */}
                    <div className={styles.formSection}>
                        <label className={styles.label}>Cut off</label>
                        <div className={styles.radioRow}>
                            <label>
                                <input
                                    type="radio"
                                    checked={evalueType === 'evalue'}
                                    onChange={() => setEvalueType('evalue')}
                                />
                                E-value
                            </label>
                            <label>
                                <input
                                    type="radio"
                                    checked={evalueType === 'bitscore'}
                                    onChange={() => setEvalueType('bitscore')}
                                />
                                Bit Score
                            </label>
                        </div>
                        <div className={styles.cutoffGrid}>
                            <div></div>
                            <div className={styles.cutoffHeader}>Sequence</div>
                            <div className={styles.cutoffHeader}>Hit</div>

                            {evalueType === 'evalue' ? (
                                <>
                                    <div className={styles.cutoffLabel}>Significance E-values</div>
                                    <input type="text" value={significanceEValueSeq}
                                           onChange={e => setSignificanceEValueSeq(e.target.value)} className={styles.input}/>
                                    <input type="text" value={significanceEValueHit}
                                           onChange={e => setSignificanceEValueHit(e.target.value)} className={styles.input}/>
                                    <div className={styles.cutoffLabel}>Report E-values</div>
                                    <input type="text" value={reportEValueSeq} onChange={e => setReportEValueSeq(e.target.value)}
                                           className={styles.input}/>
                                    <input type="text" value={reportEValueHit} onChange={e => setReportEValueHit(e.target.value)}
                                           className={styles.input}/>
                                </>
                            ) : (
                                <>
                                    <div className={styles.cutoffLabel}>Significance Bit scores</div>
                                    <input type="text" value={significanceBitScoreSeq}
                                           onChange={e => setSignificanceBitScoreSeq(e.target.value)} className={styles.input}/>
                                    <input type="text" value={significanceBitScoreHit}
                                           onChange={e => setSignificanceBitScoreHit(e.target.value)} className={styles.input}/>
                                    <div className={styles.cutoffLabel}>Report Bit scores</div>
                                    <input type="text" value={reportBitScoreSeq} onChange={e => setReportBitScoreSeq(e.target.value)}
                                           className={styles.input}/>
                                    <input type="text" value={reportBitScoreHit} onChange={e => setReportBitScoreHit(e.target.value)}
                                           className={styles.input}/>
                                </>
                            )}
                        </div>
                    </div>

                    {/* Gap penalties */}
                    <div className={styles.formSection}>
                        <label className={styles.label}>Gap penalties</label>
                        <div className={styles.gapRow}>
                            <div>
                                <div>Open</div>
                                <input type="text" value={gapOpen} onChange={e => setGapOpen(e.target.value)}
                                       className={styles.inputSmall}/>
                            </div>
                            <div>
                                <div>Extend</div>
                                <input type="text" value={gapExtend} onChange={e => setGapExtend(e.target.value)}
                                       className={styles.inputSmall}/>
                            </div>
                            <div>
                                <div>Substitution scoring matrix</div>
                                <select value={subMatrix} onChange={e => setSubMatrix(e.target.value)} className={styles.selectSmall}>
                                    {mxChoices.map(choice => (
                                        <option key={choice.value} value={choice.value}>{choice.label}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                    </div>
                </div>
                <div className={styles.rightPane}>
                    <PyhmmerSearchInput
                        sequence={sequence}
                        setSequence={setSequence}
                        handleSubmit={handleSubmit}
                    />
                </div>
            </div>

            {/* Results two-column layout */}
            <div className={styles.resultsContainer} style={{ display: 'flex', gap: 24 }}>
                <div style={{ flex: 0.7, minWidth: 220, maxWidth: 320, borderRight: '1px solid #eee', paddingRight: 16 }}>
                    <PyhmmerSearchHistory
                        history={history}
                        onSelect={handleSelectHistory}
                        selectedJobId={selectedJobId}
                    />
                </div>
                <div style={{ flex: 2, paddingLeft: 16 }}>
                    <PyhmmerResultsTable
                        results={results}
                        loading={loading}
                        error={error}
                        jobId={selectedJobId}
                    />
                </div>
            </div>
        </section>
    );
};

export default PyhmmerSearchForm;