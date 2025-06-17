import React, { useState } from 'react';
import styles from './PyhmmerSearchForm.module.scss';

const PyhmmerSearchForm: React.FC = () => {
    const [activeTab, setActiveTab] = useState('phmmer');
    const [evalueType, setEvalueType] = useState<'evalue' | 'bitscore'>('evalue');
    const [sequence, setSequence] = useState('');
    const [database, setDatabase] = useState('Reference Proteomes (2025_01)');
    const [significanceEValueSeq, setSignificanceEValueSeq] = useState('0.01');
    const [significanceEValueHit, setSignificanceEValueHit] = useState('0.03');
    const [reportEValueSeq, setReportEValueSeq] = useState('1');
    const [reportEValueHit, setReportEValueHit] = useState('1');
    const [gapOpen, setGapOpen] = useState('0.02');
    const [gapExtend, setGapExtend] = useState('0.4');
    const [subMatrix, setSubMatrix] = useState('BLOSUM62');
    const [biasFilter, setBiasFilter] = useState(false);

    return (
        <div className={styles.pyhmmerFormWrapper}>

            <h3 className={styles.sectionTitle}>protein sequence vs protein sequence database</h3>

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
                        Paste in your sequence, use the <a href="#">example</a>, drag a file over or <a href="#">choose a file to upload</a>
                    </div>
                </div>
                <div className={styles.buttonRow}>
                    <button className={styles.submitBtn}>Submit</button>
                    <button className={styles.resetBtn}>Reset</button>
                    <button className={styles.cleanBtn}>Clean</button>
                </div>
            </div>

            {/* Sequence database */}
            <div className={styles.formSection}>
                <label className={styles.label}>Sequence database</label>
                <select className={styles.select} value={database} onChange={e => setDatabase(e.target.value)}>
                    <option>Reference Proteomes (2025_01)</option>
                    {/* Add more options as needed */}
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
                    <input type="text" value={significanceEValueSeq} onChange={e => setSignificanceEValueSeq(e.target.value)} className={styles.input} />
                    <input type="text" value={significanceEValueHit} onChange={e => setSignificanceEValueHit(e.target.value)} className={styles.input} />
                    <div className={styles.cutoffLabel}>Report E-values</div>
                    <input type="text" value={reportEValueSeq} onChange={e => setReportEValueSeq(e.target.value)} className={styles.input} />
                    <input type="text" value={reportEValueHit} onChange={e => setReportEValueHit(e.target.value)} className={styles.input} />
                </div>
            </div>

            {/* Gap penalties */}
            <div className={styles.formSection}>
                <label className={styles.label}>Gap penalties</label>
                <div className={styles.gapRow}>
                    <div>
                        <div>Open</div>
                        <input type="text" value={gapOpen} onChange={e => setGapOpen(e.target.value)} className={styles.inputSmall} />
                    </div>
                    <div>
                        <div>Extend</div>
                        <input type="text" value={gapExtend} onChange={e => setGapExtend(e.target.value)} className={styles.inputSmall} />
                    </div>
                    <div>
                        <div>Substitution scoring matrix</div>
                        <select value={subMatrix} onChange={e => setSubMatrix(e.target.value)} className={styles.selectSmall}>
                            <option>BLOSUM62</option>
                            {/* Add more options as needed */}
                        </select>
                    </div>
                </div>
            </div>

            {/* Filter */}
            <div className={styles.formSection}>
                <label className={styles.label}>Filter</label>
                <div>
                    <label>
                        <input
                            type="checkbox"
                            checked={biasFilter}
                            onChange={e => setBiasFilter(e.target.checked)}
                        />
                        Turn off bias composition filter
                    </label>
                </div>
            </div>
        </div>
    );
};

export default PyhmmerSearchForm;