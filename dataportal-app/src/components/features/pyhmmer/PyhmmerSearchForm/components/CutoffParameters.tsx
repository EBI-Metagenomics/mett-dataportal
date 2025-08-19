import React from 'react';
import { PyhmmerEvalueType } from '../../../../../utils/pyhmmer/pyhmmerDefaults';
import styles from './CutoffParameters.module.scss';

interface CutoffParametersProps {
    evalueType: PyhmmerEvalueType;
    // E-value parameters
    significanceEValueSeq: string;
    significanceEValueHit: string;
    reportEValueSeq: string;
    reportEValueHit: string;
    // Bit score parameters
    significanceBitScoreSeq: string;
    significanceBitScoreHit: string;
    reportBitScoreSeq: string;
    reportBitScoreHit: string;
    // Setters
    setSignificanceEValueSeq: (value: string) => void;
    setSignificanceEValueHit: (value: string) => void;
    setReportEValueSeq: (value: string) => void;
    setReportEValueHit: (value: string) => void;
    setSignificanceBitScoreSeq: (value: string) => void;
    setSignificanceBitScoreHit: (value: string) => void;
    setReportBitScoreSeq: (value: string) => void;
    setReportBitScoreHit: (value: string) => void;
    // Validation
    getFieldError: (fieldName: string) => string | undefined;
}

const CutoffParameters: React.FC<CutoffParametersProps> = ({
    evalueType,
    significanceEValueSeq,
    significanceEValueHit,
    reportEValueSeq,
    reportEValueHit,
    significanceBitScoreSeq,
    significanceBitScoreHit,
    reportBitScoreSeq,
    reportBitScoreHit,
    setSignificanceEValueSeq,
    setSignificanceEValueHit,
    setReportEValueSeq,
    setReportEValueHit,
    setSignificanceBitScoreSeq,
    setSignificanceBitScoreHit,
    setReportBitScoreSeq,
    setReportBitScoreHit,
    getFieldError
}) => {
    return (
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
                            <div className={styles.errorMessage}>{getFieldError('significanceEValueSeq')}</div>
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
                            <div className={styles.errorMessage}>{getFieldError('significanceEValueHit')}</div>
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
                            <div className={styles.errorMessage}>{getFieldError('reportEValueSeq')}</div>
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
                            <div className={styles.errorMessage}>{getFieldError('reportEValueHit')}</div>
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
                            <div className={styles.errorMessage}>{getFieldError('significanceBitScoreSeq')}</div>
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
                            <div className={styles.errorMessage}>{getFieldError('significanceBitScoreHit')}</div>
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
                            <div className={styles.errorMessage}>{getFieldError('reportBitScoreSeq')}</div>
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
                            <div className={styles.errorMessage}>{getFieldError('reportBitScoreHit')}</div>
                        )}
                    </div>
                </>
            )}
        </div>
    );
};

export default CutoffParameters;
