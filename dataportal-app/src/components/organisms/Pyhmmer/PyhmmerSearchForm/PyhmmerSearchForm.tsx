import React, {useState, useRef, useEffect} from 'react';
import styles from './PyhmmerSearchForm.module.scss';
import {PyhmmerService} from '../../../../services/pyhmmerService';
import {EXAMPLE_SEQUENCE} from "../../../../utils/appConstants";
import {PyhmmerMXChoice, PyhmmerResult} from "../../../../interfaces/Pyhmmer";
import PyhmmerResultsTable from "@components/organisms/Pyhmmer/PyhmmerResultsHandler/PyhmmerResultsTable";

const PyhmmerSearchForm: React.FC = () => {
    const [evalueType, setEvalueType] = useState<'evalue' | 'bitscore'>('evalue');
    const [sequence, setSequence] = useState('');
    const [database, setDatabase] = useState('bu_all');
    const [significanceEValueSeq, setSignificanceEValueSeq] = useState('0.01');
    const [significanceEValueHit, setSignificanceEValueHit] = useState('0.03');
    const [reportEValueSeq, setReportEValueSeq] = useState('1');
    const [reportEValueHit, setReportEValueHit] = useState('1');
    const [gapOpen, setGapOpen] = useState('0.02');
    const [gapExtend, setGapExtend] = useState('0.4');
    const [subMatrix, setSubMatrix] = useState('BLOSUM62');
    // const [biasFilter, setBiasFilter] = useState(false);

    // Results state
    const [results, setResults] = useState<PyhmmerResult[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | undefined>(undefined);

    const fileInputRef = useRef<HTMLInputElement | null>(null);

    const [databases, setDatabases] = useState<{ id: string; name: string }[]>([]);
    const [mxChoices, setMXChoices] = useState<PyhmmerMXChoice[]>([]);

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
    const mapResults = (raw: any[]): PyhmmerResult[] => {
        return raw.map((hit: any) => ({
            query: hit.query || hit.query_name || '-',
            target: hit.target || hit.target_name || hit.name || '-',
            evalue: hit.evalue ?? hit.Evalue ?? '-',
            score: hit.score ?? hit.Score ?? '-',
            num_hits: hit.num_hits ?? hit.num_hits ?? '-',
            num_significant: hit.num_significant ?? hit.num_significant ?? '-',
            bias: hit.bias ?? '-',
            description: hit.description ?? hit.desc ?? '-',
        }));
    };

    const handleSubmit = async (e?: React.FormEvent) => {
        if (e) e.preventDefault();
        setLoading(true);
        setError(undefined);
        setResults([]);
        try {
            // Compose request
            const req = {
                database,
                threshold: evalueType,
                threshold_value: parseFloat(significanceEValueSeq),
                input: sequence,
            };
            const {id} = await PyhmmerService.search(req);
            const rawResults = await pollJobStatus(id);
            setResults(mapResults(rawResults));
        } catch (err: any) {
            setError(err.message || 'Error running search');
        } finally {
            setLoading(false);
        }
    };

    // Handler for using the example sequence
    const handleUseExample = (e: React.MouseEvent) => {
        e.preventDefault();
        setSequence(EXAMPLE_SEQUENCE);
    };

    // Handler for file upload
    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files && e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (event) => {
                setSequence(event.target?.result as string || '');
            };
            reader.readAsText(file);
        }
    };

    return (
        <section className={styles.pyhmmerSection}>
            <div className={styles.leftPane}>
                <p/>
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
                {/*<h3 className={styles.sectionTitle}>protein sequence vs protein sequence database</h3>*/}
                {/* Sequence Input */}
                <div className={styles.formSection}>
                    <label className={styles.label}>Sequence</label>
                    <div className={styles.sequenceInputBox}>
                        <textarea
                            className={styles.textarea}
                            value={sequence}
                            onChange={e => setSequence(e.target.value)}
                            placeholder="Paste in your sequence, use the example, drag a file over or choose a file to upload"
                            rows={7}
                        />
                        <div className={styles.sequenceInputHelp}>
                            Paste in your sequence, use the{' '}
                            <a href="#" onClick={handleUseExample}>example</a>, drag a file over or{' '}
                            <a href="#" onClick={e => {
                                e.preventDefault();
                                fileInputRef.current?.click();
                            }}>choose a file to upload</a>
                            <input
                                type="file"
                                accept=".fa,.fasta,.txt,.faa,.csv"
                                style={{display: 'none'}}
                                ref={fileInputRef}
                                onChange={handleFileChange}
                            />
                        </div>
                    </div>
                    <div className={styles.buttonRow}>
                        <button className={styles.submitBtn} onClick={handleSubmit}>Submit</button>
                        <button className={styles.resetBtn} type="button" onClick={() => setSequence('')}>Reset</button>
                        <button className={styles.cleanBtn} type="button" onClick={() => setSequence('')}>Clean</button>
                    </div>
                </div>
                {/* Results Table */}
                <div className={styles.formSection}>
                    <PyhmmerResultsTable results={results} loading={loading} error={error}/>
                </div>
            </div>
        </section>
    );
};

export default PyhmmerSearchForm;